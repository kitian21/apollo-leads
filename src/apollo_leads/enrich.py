import csv
from typing import List, Dict, Any

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

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(records)


def extract_person_phone(enriched: Dict[str, Any]) -> str | None:
    """
    Extrae SOLO teléfono de persona.
    No usa organization.phone porque ese es teléfono de empresa.
    """
    direct_phone = normalize_value(enriched.get("phone"))
    if direct_phone:
        return direct_phone

    phone_numbers = enriched.get("phone_numbers")
    if isinstance(phone_numbers, list):
        for p in phone_numbers:
            if isinstance(p, dict):
                candidate = normalize_value(
                    p.get("sanitized_number")
                    or p.get("raw_number")
                    or p.get("number")
                )
            else:
                candidate = normalize_value(p)

            if candidate:
                return candidate

    mobile_phone = normalize_value(enriched.get("mobile_phone"))
    if mobile_phone:
        return mobile_phone

    return None


def merge_record_with_enrichment(
    record: Dict[str, Any],
    enriched: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hace merge entre registro base (search) y enriquecimiento.
    Prioriza datos enriquecidos cuando existan.
    """
    email = normalize_value(enriched.get("email")) or normalize_value(record.get("email"))
    phone = extract_person_phone(enriched) or normalize_value(record.get("phone"))

    linkedin_url = (
        normalize_value(enriched.get("linkedin_url"))
        or normalize_value(enriched.get("linkedin_profile_url"))
        or normalize_value(record.get("linkedin_url"))
    )

    full_name = (
        normalize_value(enriched.get("name"))
        or normalize_value(record.get("full_name"))
    )

    title = (
        normalize_value(enriched.get("title"))
        or normalize_value(record.get("title"))
    )

    company_name = (
        normalize_value(enriched.get("organization", {}).get("name"))
        or normalize_value(record.get("company_name"))
    )

    location = (
        normalize_value(enriched.get("formatted_address"))
        or normalize_value(record.get("location"))
    )

    record["full_name"] = full_name
    record["title"] = title
    record["company_name"] = company_name
    record["linkedin_url"] = linkedin_url
    record["email"] = email
    record["phone"] = phone
    record["location"] = location
    record["contact_status"] = get_contact_status(email, phone)

    return record


def run_enrichment(input_file: str, output_file: str) -> None:
    client = ApolloClient()
    records = load_csv(input_file)

    people_ids = [
        r["apollo_person_id"]
        for r in records
        if normalize_value(r.get("apollo_person_id"))
    ]

    if not people_ids:
        print("[WARNING] No se encontraron apollo_person_id válidos en el CSV.")
        return

    batches = chunk_list(people_ids, 10)
    enriched_map: Dict[str, Dict[str, Any]] = {}

    print(f"[INFO] Enriqueciendo {len(people_ids)} contactos...")

    for batch in batches:
        enriched_people = client.bulk_enrich_people(batch)

        # if enriched_people:
        #     print("[DEBUG] Primer enriched person:", enriched_people[0])

        for person in enriched_people:
            person_id = normalize_value(person.get("id"))
            if person_id:
                enriched_map[person_id] = person

    final_records: List[Dict[str, Any]] = []

    for record in records:
        person_id = normalize_value(record.get("apollo_person_id"))
        enriched = enriched_map.get(person_id, {})

        if enriched:
            updated_record = merge_record_with_enrichment(record, enriched)
        else:
            # Si no hubo enriquecimiento, recalcula contact_status por consistencia
            email = normalize_value(record.get("email"))
            phone = normalize_value(record.get("phone"))
            record["contact_status"] = get_contact_status(email, phone)
            updated_record = record

        final_records.append(updated_record)

    save_csv(final_records, output_file)
    print(f"[OK] Enrichment completo: {output_file}")