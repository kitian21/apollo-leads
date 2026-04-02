import requests
from typing import Any, Dict, List, Optional
from .config import APOLLO_API_KEY, APOLLO_BASE_URL

class ApolloClient:
    def __init__(self) -> None:
        if not APOLLO_API_KEY:
            raise ValueError("Falta APOLLO_API_KEY en variables de entorno.")

        self.base_url = APOLLO_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": APOLLO_API_KEY,
            "accept": "application/json",
        })

    def post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        
        response = self.session.post(url, json=payload, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(
                f"Error Apollo [{response.status_code}] en {endpoint}: {response.text}"
            )

        return response.json()

    def find_company(self, company_name: str) -> Dict[str, Any] | None:
        data = self.post(
            "organizations/search",
            {
                "q_organization_name": company_name,
            },
        )
        
        orgs = data.get("organizations") or []
        if not orgs:
            return None

        # Convertimos tu input a minúsculas y quitamos espacios a los lados
        target_exacto = company_name.strip().lower()

        print(f"   -> [Buscando Match Estricto: '{company_name}']")

        for org in orgs:
            # Obtenemos el nombre exacto de Apollo
            apollo_name = (org.get("name") or "").strip().lower()
            
            # 🚀 REGLA DE ORO: Solo pasa si son idénticos. Si sobra una letra, no entra.
            if apollo_name == target_exacto:
                print(f"   -> [Aprobado] Match exacto encontrado: {org.get('name')}")
                return org

        # Si termina de revisar y ninguno es exactamente igual a tu lista, se bloquea.
        print(f"   -> [Bloqueado] Apollo devolvió opciones, pero ninguna es exactamente '{company_name}'.")
        return None

    def search_people(self, company_name: str, page: int = 1, per_page: int = 25) -> List[Dict[str, Any]]:
        data = self.post(
            "mixed_people/api_search",
            {
                "q_organization_name": company_name,
                "person_seniorities": ["manager", "director", "head", "vp", "c_suite", "founder", "owner", "partner"],
                "page": page,
                "per_page": per_page,
            },
        )
        return data.get("people") or []
    
    def bulk_enrich_people(self, ids: list[str]) -> list[dict]:
        if not ids:
            return []

        payload = {
            "details": [{"id": person_id} for person_id in ids]
        }

        data = self.post("people/bulk_match", payload)
        return data.get("people") or data.get("matches") or []