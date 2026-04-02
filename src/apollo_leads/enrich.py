import csv
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import json

from .client import ApolloClient
from .helpers import normalize_value, get_contact_status


def chunk_list(data: List[Any], size: int) -> List[List[Any]]:
    return [data[i:i + size] for i in range(0, len(data), size)]


def load_csv(input_file: str) -> List[Dict[str, Any]]:
    with open(input_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def save_csv(records: List[Dict[str, Any]], output_file: str) -> None:
    if not records:
        print("[WARNING] No hay registros para guardar.")
        return

    fieldnames = list(records[0].keys())

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(records)


def extract_person_phone(enriched: Dict[str, Any]) -> str | None:
    # 1. Búsqueda directa en la raíz
    direct_phone = normalize_value(enriched.get("phone"))
    if direct_phone:
        return direct_phone

    # 2. Búsqueda en la lista de números (puede estar en la raíz o dentro de 'contact')
    phone_numbers = enriched.get("phone_numbers") or enriched.get("contact", {}).get("phone_numbers")
    
    if isinstance(phone_numbers, list):
        for p in phone_numbers:
            if isinstance(p, dict):
                # Priorizamos el número limpio (sanitized)
                candidate = normalize_value(
                    p.get("sanitized_number") or p.get("raw_number") or p.get("number")
                )
            else:
                candidate = normalize_value(p)
                
            if candidate:
                return candidate

    # 3. Búsqueda final como teléfono móvil suelto
    mobile_phone = normalize_value(enriched.get("mobile_phone"))
    if mobile_phone:
        return mobile_phone

    return None

def merge_record_with_enrichment(record: Dict[str, Any], enriched: Dict[str, Any]) -> Dict[str, Any]:
    email = normalize_value(enriched.get("email")) or normalize_value(record.get("email"))
    phone = extract_person_phone(enriched) or normalize_value(record.get("phone"))
    linkedin_url = (
        normalize_value(enriched.get("linkedin_url"))
        or normalize_value(enriched.get("linkedin_profile_url"))
        or normalize_value(record.get("linkedin_url"))
    )
    full_name = normalize_value(enriched.get("name")) or normalize_value(record.get("full_name"))
    title = normalize_value(enriched.get("title")) or normalize_value(record.get("title"))
    company_name = (
        normalize_value(enriched.get("organization", {}).get("name"))
        or normalize_value(record.get("company_name"))
    )
    location = normalize_value(enriched.get("formatted_address")) or normalize_value(record.get("location"))

    email_status = normalize_value(enriched.get("email_status"))

    record["full_name"] = full_name
    record["title"] = title
    record["company_name"] = company_name
    record["linkedin_url"] = linkedin_url
    record["email"] = email
    record["phone"] = phone
    record["location"] = location
    record["contact_status"] = get_contact_status(email, phone)
    record["email_status"] = email_status

    return record


def run_enrichment(input_path: str, output_file: str) -> None:
    client = ApolloClient()
    records = []
    
    path_obj = Path(input_path)
    
    if path_obj.is_file():
        print(f"[INFO] Cargando un solo archivo: {path_obj.name}")
        records.extend(load_csv(str(path_obj)))
    elif path_obj.is_dir():
        csv_files = list(path_obj.glob("*.csv"))
        print(f"[INFO] Escaneando carpeta. Se encontraron {len(csv_files)} archivos CSV.")
        for f in csv_files:
            records.extend(load_csv(str(f)))
    else:
        print(f"[ERROR] La ruta de entrada no existe: {input_path}")
        return

    if not records:
        print("[WARNING] No hay registros válidos para procesar.")
        return

    people_ids = [
        r["apollo_person_id"]
        for r in records
        if normalize_value(r.get("apollo_person_id"))
    ]

    if not people_ids:
        print("[WARNING] No se encontraron apollo_person_id válidos en los CSV.")
        return

    batches = chunk_list(people_ids, 10)
    enriched_map: Dict[str, Dict[str, Any]] = {}

    print(f"[INFO] Enriqueciendo {len(people_ids)} contactos en bloque...")

    batches = chunk_list(people_ids, 10)
    enriched_map: Dict[str, Dict[str, Any]] = {}

    print(f"[INFO] Enriqueciendo {len(people_ids)} contactos en bloque...")

    # 🚀 1. Creamos una lista vacía antes del ciclo
    todas_las_radiografias = []

    for batch in tqdm(batches, desc="Enriqueciendo leads", unit="lote"):
        enriched_people = client.bulk_enrich_people(batch)

        # 🚀 2. Acumulamos los perfiles de este lote en la lista maestra
        todas_las_radiografias.extend(enriched_people)

        for person in enriched_people:
            person_id = normalize_value(person.get("id"))
            if person_id:
                enriched_map[person_id] = person

    # 🚀 3. Guardamos el archivo UNA SOLA VEZ al terminar todo el ciclo
    with open("radiografia_apollo.json", "w", encoding="utf-8") as f:
        json.dump(todas_las_radiografias, f, indent=4, ensure_ascii=False)
    
    print(f"\n[OK] ¡Radiografía completa de {len(todas_las_radiografias)} contactos guardada en 'radiografia_apollo.json'!")

    # ... (aquí sigue el resto de tu código normal creando final_records)

    final_records: List[Dict[str, Any]] = []

    for record in records:
        person_id = normalize_value(record.get("apollo_person_id"))
        enriched = enriched_map.get(person_id, {})

        if enriched:
            updated_record = merge_record_with_enrichment(record, enriched)
        else:
            email = normalize_value(record.get("email"))
            phone = normalize_value(record.get("phone"))
            record["contact_status"] = get_contact_status(email, phone)
            record["email_status"] = None
            updated_record = record

        final_records.append(updated_record)

    save_csv(final_records, output_file)
    print(f"\n[OK] Enrichment masivo completo. Consolidado guardado en: {output_file}")