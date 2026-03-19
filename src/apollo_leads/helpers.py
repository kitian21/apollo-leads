import re
from typing import Any, Dict, Optional
from .config import EMPTY_VALUES


def normalize_value(value: Any) -> Optional[str]:
    if value is None:
        return None

    value_str = str(value).strip()
    if value_str in EMPTY_VALUES:
        return None

    return value_str


def is_valid_email(email: Any) -> bool:
    email = normalize_value(email)
    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone: Any) -> bool:
    phone = normalize_value(phone)
    if not phone:
        return False

    digits = "".join(ch for ch in phone if ch.isdigit())
    return len(digits) >= 6


def get_contact_status(email: Any, phone: Any) -> str:
    email_ok = is_valid_email(email)
    phone_ok = is_valid_phone(phone)

    if email_ok and phone_ok:
        return "email y telefono encontrados"
    if email_ok:
        return "email encontrado"
    if phone_ok:
        return "telefono encontrado"
    return "sin contacto encontrado"


def build_full_name(person: Dict[str, Any]) -> Optional[str]:
    full_name = normalize_value(person.get("name"))
    if full_name:
        return full_name

    first_name = normalize_value(person.get("first_name"))
    last_name = normalize_value(person.get("last_name"))
    last_name_obfuscated = normalize_value(person.get("last_name_obfuscated"))

    last_part = last_name or last_name_obfuscated
    parts = [p for p in [first_name, last_part] if p]

    return " ".join(parts) if parts else None


def extract_location(person: Dict[str, Any]) -> Optional[str]:
    city = normalize_value(person.get("city"))
    state = normalize_value(person.get("state"))
    country = normalize_value(person.get("country"))

    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts) if parts else None


def extract_phone(person: Dict[str, Any]) -> Optional[str]:
    phone_numbers = person.get("phone_numbers")

    if isinstance(phone_numbers, list):
        for p in phone_numbers:
            if isinstance(p, dict):
                candidate = normalize_value(
                    p.get("sanitized_number") or p.get("raw_number") or p.get("number")
                )
            else:
                candidate = normalize_value(p)

            if candidate:
                return candidate

    return normalize_value(person.get("phone"))

def is_relevant_role(title: str | None) -> str:
    if not title:
        return "No"

    t = title.lower()

    # Roles que SÍ interesan
    relevant_keywords = [
        "sales",
        "marketing",
        "growth",
        "business development",
        "revenue",
        "commercial",
        "partnership",
    ]

    # Roles que NO interesan
    irrelevant_keywords = [
        "hr",
        "human resources",
        "people",
        "office",
        "admin",
        "support",
        "customer service",
    ]

    if any(word in t for word in irrelevant_keywords):
        return "No"

    if any(word in t for word in relevant_keywords):
        return "Yes"

    return "No"