import os
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("", "")
APOLLO_BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/api/v1")

# Nuevas credenciales de AWS
APOLLO_WEBHOOK_URL = ""
AWS_ACCESS_KEY = "" # Pega tu Access Key aquí
AWS_SECRET_KEY = ""     # Pega tu Secret Key aquí
AWS_REGION = "us-east-2"

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