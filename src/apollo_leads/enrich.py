import pandas as pd
import boto3
import json
import time
import os
from pathlib import Path

# Importaciones de tu proyecto en In-Data
from .client import ApolloClient
from .helpers import normalize_value, get_contact_status
from .config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION

# Configuración de AWS y archivos temporales
BUCKET_NAME = "baudata-2025"
MAILBOX_KEY = "apollo-contacts/phone_numbers/telefonos_recibidos.json"
PATH_SIN_ENRIQUECER = Path("data/temp/peticion_sin_enriquecer.json")
PATH_ENRIQUECIDO = Path("data/temp/peticion_enriquecida.json")

def save_json_local(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def run_enrichment(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        print(f"❌ Error: No se encontró {input_file}")
        return

    try:
        # 1. GENERAR JSON "SIN ENRIQUECER" (Estado inicial del CSV)
        df = pd.read_csv(input_file, sep=';', encoding='utf-8-sig', dtype=str).fillna("")
        api_ids = df['apollo_person_id'].replace("", None).dropna().unique().tolist()
        
        save_json_local({"total": len(api_ids), "ids": api_ids}, PATH_SIN_ENRIQUECER)
        print(f"💾 JSON 1 (Sin Enriquecer) guardado en data/temp/")

        # 2. LLAMADA A APOLLO Y CAPTURA DE INFO INMEDIATA (Email, LinkedIn, Cargo)
        client = ApolloClient()
        print(f"📡 Llamando a Apollo... capturando perfiles básicos.")
        res_api = client.bulk_enrich_people(api_ids)
        
        # Apollo devuelve 'matches' o 'people' con la info que no requiere revelar teléfonos
        contactos_api = res_api.get("matches", []) or res_api.get("people", [])
        data_api_map = {c['id']: c for c in contactos_api if 'id' in c}

        # Guardamos el JSON 2 (Enriquecido con lo que dio la API al instante)
        save_json_local(data_api_map, PATH_ENRIQUECIDO)
        print(f"💾 JSON 2 (Enriquecido parcial) guardado con info de la API.")

        # 3. ESPERA DEL NÚMERO CELULAR (Desde AWS S3 - Ajustado a 3 min)
        s3 = boto3.client('s3', region_name=AWS_REGION, 
                         aws_access_key_id=AWS_ACCESS_KEY, 
                         aws_secret_access_key=AWS_SECRET_KEY)
        
        # Limpiamos el buzón de S3 antes de esperar
        try: s3.delete_object(Bucket=BUCKET_NAME, Key=MAILBOX_KEY)
        except: pass

        print(f"⏳ Esperando confirmación de números celulares (Tiempo máximo: 2 minutos)...")
        
        telefonos_map = {}
        intentos = 0
        max_intentos = 8  # 8 intentos de 15 segundos = 2 minutos
        
        while intentos < max_intentos:
            time.sleep(15)
            try:
                res_s3 = s3.get_object(Bucket=BUCKET_NAME, Key=MAILBOX_KEY)
                # El Lambda solo envía {id: numero} o una lista de contactos con solo el número
                data_aws = json.loads(res_s3['Body'].read().decode('utf-8'))
                
                # Normalizamos lo que venga de AWS (si es lista lo pasamos a dict)
                if isinstance(data_aws, list):
                    for item in data_aws:
                        if isinstance(item, dict) and item.get('id'):
                            # Buscamos el número en el formato que envíe tu Lambda
                            num = item.get('phone') or item.get('phone_number')
                            if not num and item.get('phone_numbers'):
                                num = item['phone_numbers'][0].get('sanitized_number')
                            telefonos_map[item['id']] = num
                else:
                    telefonos_map = data_aws

                print(f"📥 ¡AWS respondió en el intento {intentos + 1}! Procesando números...")
                s3.delete_object(Bucket=BUCKET_NAME, Key=MAILBOX_KEY)
                break

            except s3.exceptions.NoSuchKey:
                intentos += 1
                if intentos % 4 == 0:
                    min_transcurridos = (intentos * 15) // 60
                    print(f"   ... S3 aún sin números ({min_transcurridos} min transcurridos)")
            except Exception as e:
                print(f"❌ Error leyendo S3: {e}")
                break

        # PLAN DE CONTINGENCIA
        if intentos >= max_intentos:
            print("⚠️ Límite de 3 minutos alcanzado. No llegaron teléfonos desde Apollo.")
            print("➡️ Avanzando al guardado con la información rescatada...")

        # 4. CRUCE FINAL HÍBRIDO (Se ejecuta siempre)
        print("🔄 Realizando cruce de información en el CSV...")
        for idx, row in df.iterrows():
            p_id = row['apollo_person_id']
            
            # A. Sumamos info de la API (Email, LinkedIn, Cargo)
            if p_id in data_api_map:
                p = data_api_map[p_id]
                if p.get("email"): df.at[idx, 'email'] = p["email"]
                if p.get("linkedin_url"): df.at[idx, 'linkedin_url'] = p["linkedin_url"]
                if p.get("title"): df.at[idx, 'title'] = p["title"]
                if p.get("name"): df.at[idx, 'full_name'] = p["name"]

            # B. Sumamos el número celular de AWS (si existe)
            if p_id in telefonos_map:
                celular = str(telefonos_map[p_id]).strip()
                if celular and celular != "None":
                    # El apóstrofe protege el número para que Excel no lo rompa
                    df.at[idx, 'phone'] = f"'{celular}"

            # C. Recalculamos el status final
            e_final = str(df.at[idx, 'email']).strip()
            t_final = str(df.at[idx, 'phone']).replace("'", "").strip()
            df.at[idx, 'contact_status'] = get_contact_status(e_final, t_final)

        # 5. GUARDAR RESULTADO (Garantizado)
        df.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')
        print(f"🚀 ¡Éxito! Archivo de data mining generado en: {output_file}")

    except Exception as e:
        print(f"[ERROR CRÍTICO] {e}")