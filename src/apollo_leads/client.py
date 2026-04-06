import requests
import time
from typing import Any, Dict, List, Optional
# Importamos la nueva variable desde config
from .config import APOLLO_API_KEY, APOLLO_BASE_URL, APOLLO_WEBHOOK_URL

class ApolloClient:
    def __init__(self) -> None:
        if not APOLLO_API_KEY:
            raise ValueError("Falta APOLLO_API_KEY en config.py.")

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
        try:
            response = self.session.post(url, json=payload, timeout=30)
            
            # Si Apollo nos pide esperar (Rate Limit), lo manejamos
            if response.status_code == 429:
                print("⚠️ Rate limit alcanzado. Esperando 5 segundos...")
                time.sleep(5)
                return self.post(endpoint, payload)

            if response.status_code != 200:
                raise RuntimeError(
                    f"Error Apollo [{response.status_code}] en {endpoint}: {response.text}"
                )

            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Falla de conexión con Apollo: {e}")

    def find_company(self, company_name: str) -> Dict[str, Any] | None:
        """Busca una empresa y retorna el match exacto para asegurar integridad en baudata."""
        data = self.post(
            "organizations/search",
            {"q_organization_name": company_name}
        )
        
        orgs = data.get("organizations") or []
        if not orgs:
            return None

        target_exacto = company_name.strip().lower()
        print(f"   -> [Buscando Match Estricto: '{company_name}']")

        for org in orgs:
            apollo_name = (org.get("name") or "").strip().lower()
            
            # REGLA DE ORO: Match exacto para evitar cruces de datos erróneos
            if apollo_name == target_exacto:
                print(f"   -> [Aprobado] Match exacto: {org.get('name')}")
                return org

        print(f"   -> [Bloqueado] No hay match exacto para '{company_name}'.")
        return None

    def search_people(self, company_name: str, page: int = 1, per_page: int = 25) -> List[Dict[str, Any]]:
        """Busca personas en una empresa específica filtrando por niveles de gerencia."""
        payload = {
            "q_organization_name": company_name,
            "person_seniorities": ["manager", "director", "head", "vp", "c_suite", "founder", "owner", "partner"],
            "page": page,
            "per_page": per_page,
        }
        data = self.post("mixed_people/api_search", payload)
        return data.get("people") or []
    
    def bulk_enrich_people(self, person_ids: List[str]) -> Dict[str, Any]:
        """
        Solicita el enriquecimiento masivo. 
        Retorna el Dict de confirmación de Apollo (no una lista).
        """
        payload = {
            "details": [{"id": pid} for pid in person_ids],
            "reveal_phone_number": True,
            "webhook_url": APOLLO_WEBHOOK_URL
        }
        return self.post("people/bulk_match", payload)