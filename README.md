# 🚀 Apollo Leads

Herramienta simple para buscar y estructurar leads B2B usando la API de Apollo.

## Qué hace

- Busca una empresa en Apollo
- Encuentra empleados con cargos clave (`Manager`, `Director`, `Head`, `VP`)
- Limpia y estructura los datos
- Exporta resultados a CSV
- Separa búsqueda y enriquecimiento en flujos independientes

## Enfoque

El proyecto trabaja en dos etapas:

- **Search** → identifica perfiles relevantes
- **Enrich** → intenta obtener datos de contacto adicionales

Esto permite validar el targeting antes de enriquecer datos o escalar el proceso.

## Modos disponibles

### Search
Busca empleados de una empresa y genera un CSV base.

```bash
python main.py --mode search --company "HubSpot" --output data/raw/hubspot.csv
```

Enrich
```bash
Toma un CSV generado por search y realiza enrichment sobre esos contactos.

python main.py --mode enrich --input data/raw/hubspot.csv --output data/processed/hubspot_enriched.csv
```
Output
Los archivos generados incluyen campos como
full_name
title
company_name
linkedin_url
email
phone
location
contact_status
is_relevant_role
has_email_flag
has_direct_phone_flag

Nota importante
La búsqueda no devuelve directamente emails ni teléfonos finales en todos los casos.
Apollo puede devolver señales como has_email o has_direct_phone, pero eso no garantiza que el dato venga disponible en el enrichment inmediato.
En la práctica, el email suele tener mejor cobertura que el teléfono.

Instalación
```bash
pip install -r requirements.txt
```

Configuración
Crea un archivo .env con:
```bash
APOLLO_API_KEY=tu_api_key
APOLLO_BASE_URL=https://api.apollo.io/api/v1
```