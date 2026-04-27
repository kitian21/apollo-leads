import argparse
import re
import csv
import os
import glob
from pathlib import Path
from src.apollo_leads.search import run_search
from src.apollo_leads.enrich import run_enrichment

def save_csv(records, output_file):
    if not records:
        return
    
    # Crea la carpeta si no existe
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(records[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(records)

def main():
    parser = argparse.ArgumentParser(description="Apollo Leads B2B Extractor")
    parser.add_argument("--mode", choices=["search", "enrich"], required=True, help="Modo de ejecución")
    
    # Argumentos para Search
    parser.add_argument("--company", type=str, help="Nombre de una empresa individual para buscar")
    parser.add_argument("--file", type=str, help="Ruta a un archivo .txt con la lista de empresas")
    parser.add_argument("--limit", type=int, default=100, help="Límite de leads por empresa")
    
    # Argumentos para Enrich y outputs
    parser.add_argument("--input", type=str, help="Archivo o carpeta CSV de entrada (solo para enrich)")
    parser.add_argument("--output", type=str, help="Archivo CSV de salida (requerido si input es un solo archivo)")

    args = parser.parse_args()

    if args.mode == "search":
        # MODO MASIVO: Búsqueda desde un archivo .txt
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    # Lee las líneas, quita espacios extra y omite líneas en blanco
                    empresas = [line.strip() for line in f if line.strip()]
                
                print(f"[INFO] Iniciando búsqueda masiva para {len(empresas)} empresas.")
                
                for empresa in empresas:
                    print(f"\n{'='*40}")
                    print(f"🚀 Procesando: {empresa}")
                    print(f"{'='*40}")
                    
                    records = run_search(company_input=empresa, limit=args.limit)
                    
                    if records:
                        # 1. Limpieza profunda: Expresión regular para caracteres prohibidos en Windows
                        nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", empresa)
                        
                        # 2. Limpieza de formato: Quitamos espacios, comas y puntos
                        nombre_limpio = nombre_limpio.replace(" ", "_").replace(",", "").replace(".", "")
                        
                        out_path = f"data/raw/{nombre_limpio}.csv"
                        save_csv(records, out_path)
                        print(f"[OK] {len(records)} leads guardados en {out_path}")
                    else:
                        print(f"[WARNING] No se extrajeron leads para {empresa}.")
            except FileNotFoundError:
                print(f"[ERROR] No se encontró el archivo: {args.file}")

        # MODO INDIVIDUAL: Búsqueda de una sola empresa
        elif args.company and args.output:
            records = run_search(company_input=args.company, limit=args.limit)
            save_csv(records, args.output)
            print(f"\n[OK] Guardado en {args.output}")
        else:
            print("[ERROR] Para buscar necesitas proveer --company y --output, o utilizar --file")

    elif args.mode == "enrich":
        if not args.input:
            print("[ERROR] El modo enrich requiere --input (puede ser una carpeta o un archivo .csv)")
            return
            
        input_path = args.input

        # 1. VERIFICAR SI LA ENTRADA ES UNA CARPETA (PROCESAMIENTO MASIVO)
        if os.path.isdir(input_path):
            print(f"[INFO] Modo masivo detectado. Escaneando directorio: {input_path}")
            
            # Buscar todos los archivos .csv en la ruta especificada
            archivos_csv = glob.glob(os.path.join(input_path, "*.csv"))
            
            if not archivos_csv:
                print(f"[WARNING] No se encontraron archivos .csv en {input_path}")
                return
            
            print(f"[INFO] Se procesarán {len(archivos_csv)} archivos.")
            
            # Iterar sobre cada archivo encontrado
            for archivo in archivos_csv:
                nombre_base = os.path.basename(archivo)
                nombre_sin_ext = os.path.splitext(nombre_base)[0]
                
                # Configurar la ruta de salida automáticamente en la carpeta processed
                ruta_salida = os.path.join("data", "processed", f"{nombre_sin_ext}_Enriquecido.csv")
                
                print(f"\n{'='*50}")
                print(f"🚀 Iniciando cruce para: {nombre_base}")
                print(f"{'='*50}")
                
                # Llamada a la función de enriquecimiento
                run_enrichment(archivo, ruta_salida)
                
            print("\n[OK] Procesamiento masivo completado exitosamente.")

        # 2. VERIFICAR SI LA ENTRADA ES UN ARCHIVO INDIVIDUAL
        elif os.path.isfile(input_path):
            if not args.output:
                print("[ERROR] Debes especificar un --output cuando procesas un archivo individual.")
                return
            run_enrichment(input_path, args.output)
            
        else:
            print(f"[ERROR CRÍTICO] La ruta especificada no es válida: {input_path}")

if __name__ == "__main__":
    main()