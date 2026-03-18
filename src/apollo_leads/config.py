import os
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("hSbW7QyQBQtIB_I0jGjPlA", "hSbW7QyQBQtIB_I0jGjPlA")
APOLLO_BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/api/v1")

TARGET_TITLES = ["Manager", "Director", "Head", "VP"]

EMPTY_VALUES = {None, "", "N/A", "n/a", "NA", "None", "-"}

OUTPUT_FIELDS = [
    "apollo_person_id",
    "full_name",
    "title",
    "seniority",
    "company_name",
    "linkedin_url",
    "email",
    "phone",
    "location",
    "contact_status",
    "has_email_flag",
    "has_direct_phone_flag",
]