from typing import Any, Dict, List

from .client import ApolloClient
from .config import TARGET_TITLES
from .helpers import (
    is_relevant_role,
    normalize_value,
    build_full_name,
    extract_location,
    extract_phone,
    get_contact_status,
)


def normalize_person_record(person: Dict[str, Any], fallback_company_name: str) -> Dict[str, Any]:
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

    # --- NUEVOS CAMPOS CAPTURADOS EN SEARCH ---
    seniority = normalize_value(person.get("seniority"))
    email_status = normalize_value(person.get("email_status"))
    
    departments_raw = person.get("departments")
    if isinstance(departments_raw, list) and departments_raw:
        departments = ", ".join([str(d) for d in departments_raw if d])
    else:
        departments = None

    return {
        "apollo_person_id": normalize_value(person.get("id")),
        "full_name": full_name,
        "title": title,
        "seniority": seniority,
        "departments": departments,
        "company_name": company_name,
        "linkedin_url": linkedin_url,
        "email": email,
        "email_status": email_status,
        "phone": phone,
        "location": location,
        "contact_status": get_contact_status(email, phone),
        "has_email_flag": normalize_value(person.get("has_email")),
        "has_direct_phone_flag": normalize_value(person.get("has_direct_phone")),
        "is_relevant_role": is_relevant_role(title),
    }


def run_search(company_input: str, limit: int = 100) -> List[Dict[str, Any]]:
    client = ApolloClient()

    company = client.find_company(company_input)
    if not company:
        print(f"[WARNING] No fue posible identificar la empresa: {company_input}")
        return []

    all_people = []
    page = 1
    per_page = 25

    print(f"[INFO] Buscando leads en {company['company_name']}...")

    # Implementación de paginación para no perder leads
    while len(all_people) < limit:
        raw_people = client.search_people(
            company_name=company["company_name"],
            titles=TARGET_TITLES,
            page=page,
            per_page=per_page,
        )

        if not raw_people:
            break

        all_people.extend(raw_people)
        print(f"[DEBUG] Página {page} trajo {len(raw_people)} registros. Acumulado: {len(all_people)}")

        if len(raw_people) < per_page:
            break
        
        page += 1

    all_people = all_people[:limit]

    return [
        normalize_person_record(person, fallback_company_name=company["company_name"])
        for person in all_people
    ]