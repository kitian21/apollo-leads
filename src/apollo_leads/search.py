import time
from typing import Any, Dict, List
from tqdm import tqdm

from .client import ApolloClient
from .helpers import (
    is_relevant_role,
    normalize_value,
    build_full_name,
    extract_location,
    extract_phone,
    get_contact_status,
)

def normalize_person_record(person: Dict[str, Any], fallback_company_name: str, relevant_role: str) -> Dict[str, Any]:
    """
    Normaliza el registro. Recibe relevant_role ya calculado para ahorrar procesamiento.
    """
    full_name = build_full_name(person)
    title = normalize_value(person.get("title"))

    company_name = (
        normalize_value(person.get("organization", {}).get("name"))
        or normalize_value(person.get("company_name"))
        or fallback_company_name
    )

    linkedin_url = (
        normalize_value(person.get("linkedin_url"))
        or normalize_value(person.get("linkedin_profile_url"))
    )

    email = normalize_value(person.get("email"))
    phone = extract_phone(person)
    location = extract_location(person)

    return {
        "apollo_person_id": normalize_value(person.get("id")),
        "full_name": full_name,
        "title": title,
        "company_name": company_name,
        "linkedin_url": linkedin_url,
        "email": email,
        "phone": phone,
        "location": location,
        "contact_status": get_contact_status(email, phone),
        "has_email_flag": normalize_value(person.get("has_email")),
        "has_direct_phone_flag": normalize_value(person.get("has_direct_phone")),
        "is_relevant_role": relevant_role,
    }


def run_search(company_input: str, limit: int = 100) -> List[Dict[str, Any]]:
    client = ApolloClient()
    company_data = client.find_company(company_input)

    if not company_data:
        return []

    # MEJORA: Comparación insensible a mayúsculas/minúsculas y espacios extra
    found_name = company_data.get("name", "").strip().lower()
    input_name = company_input.strip().lower()

    if found_name != input_name:
        print(f"[SKIP] '{company_data.get('name')}' no coincide suficientemente con '{company_input}'")
        return []

    all_normalized_people = []
    page = 1
    per_page = 25

    print(f"[INFO] Buscando alta gerencia en: {company_data['name']}")
    pbar = tqdm(total=limit, desc="Progreso", unit=" lead")

    while len(all_normalized_people) < limit:
        raw_people = client.search_people(
            company_name=company_data["name"],
            page=page,
            per_page=per_page,
        )

        if not raw_people:
            break

        for person in raw_people:
            if len(all_normalized_people) >= limit:
                break

            title = normalize_value(person.get("title"))
            relevance = is_relevant_role(title)

            # Si el rol es relevante ("Yes"), normalizamos y guardamos de una vez
            if relevance == "Yes":
                norm_record = normalize_person_record(
                    person, 
                    fallback_company_name=company_data["name"],
                    relevant_role=relevance
                )
                all_normalized_people.append(norm_record)
                pbar.update(1)

        if len(raw_people) < per_page:
            break
        
        page += 1
        # MEJORA: Pequeña pausa para respetar el Rate Limit de la API (RPM)
        time.sleep(0.5) 

    pbar.close()
    return all_normalized_people