import os
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("", "")
APOLLO_BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/api/v1")

TARGET_TITLES = [
    "Administrador", "Administración", "Administration", "Admin",
    "Adquisiciones", "Compras", "Procurement", "Purchasing", "Buyer",
    "Logística", "Logistics", "Supply Chain", "Operaciones", "Operations",
    "Warehouse",
]

EMPTY_VALUES = {None, "", "N/A", "n/a", "NA", "None", "-"}

OUTPUT_FIELDS = [
    "apollo_person_id",
    "full_name",
    "title",
    "company_name",
    "email",
    "phone",
    "linkedin_url",
    "location",
    "contact_status",
    "has_email_flag",
    "has_direct_phone_flag",
    "is_relevant_role",
]