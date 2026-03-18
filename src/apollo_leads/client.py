from typing import Any, Dict, List, Optional
import requests

from .config import APOLLO_API_KEY, APOLLO_BASE_URL


class ApolloClient:
    def __init__(self) -> None:
        if not APOLLO_API_KEY:
            raise ValueError("Falta APOLLO_API_KEY en variables de entorno.")

        self.base_url = APOLLO_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": APOLLO_API_KEY,
            "accept": "application/json",
        }

    def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(
                f"Error Apollo [{response.status_code}] en {endpoint}: {response.text}"
            )

        return response.json()

    def find_company(self, company_input: str) -> Optional[Dict[str, Any]]:
        data = self.post(
            "mixed_companies/search",
            {
                "q_organization_name": company_input,
                "page": 1,
                "per_page": 10,
            },
        )

        organizations = data.get("organizations") or data.get("accounts") or []
        if not organizations:
            return None

        company = organizations[0]
        return {
            "company_id": company.get("id"),
            "company_name": company.get("name"),
            "domain": company.get("website_url") or company.get("primary_domain") or company.get("domain"),
            "raw": company,
        }

    def search_people(self, company_name: str, titles: List[str], page: int = 1, per_page: int = 25) -> List[Dict[str, Any]]:
        data = self.post(
            "mixed_people/api_search",
            {
                "q_organization_name": company_name,
                "person_titles": titles,
                "page": page,
                "per_page": per_page,
            },
        )
        return data.get("people") or []