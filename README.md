# Apollo Leads B2B Extractor

Herramienta de línea de comandos (CLI) diseñada para la prospección, extracción y enriquecimiento automatizado de leads B2B mediante la API de Apollo. 

El sistema está optimizado para identificar tomadores de decisión reales (C-Level, Directores, Gerentes y Jefaturas) en áreas de Adquisiciones, Operaciones, Logística y Administración, descartando automáticamente perfiles comerciales, operativos de terreno o de nivel junior.

## Arquitectura del Proceso

El proyecto opera bajo un modelo de **dos etapas (Search & Enrich)** para proteger la cuota de la API y garantizar la calidad de los datos:

1. **Search (Búsqueda y Filtrado):** Consulta la base de datos de Apollo, extrae metadata de los empleados y aplica un filtro estricto en Python para retener únicamente los cargos de alto valor estratégico. 
2. **Enrich (Enriquecimiento):** Toma un archivo CSV previamente validado y consume créditos de la API exclusivamente para revelar datos de contacto (email y teléfono) de los perfiles clave.

## Reglas de Negocio (Filtros)

El motor de búsqueda aplica filtros estrictos para garantizar la relevancia de los contactos:
* **Perfiles Objetivo:** `Adquisiciones`, `Compras`, `Procurement`, `Logística`, `Supply Chain`, `Administración`, `Operaciones`, `Finanzas`.
* **Perfiles Descartados:** `Ventas`, `Marketing`, `Recursos Humanos`.
* **Filtro Anti-Junior:** Se excluyen automáticamente cargos como `Supervisor`, `Analista`, `Asistente`, `Técnico`, `Practicante` y operativos de turno.

## Instalación

1. Clona el repositorio.
2. Instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```
3. Crea un archivo .env en la raíz del proyecto con tus credenciales:
```Fragmento de código
APOLLO_API_KEY=tu_api_key_aqui
APOLLO_BASE_URL=[https://api.apollo.io/api/v1](https://api.apollo.io/api/v1)
```
## Uso de la Herramienta
El CLI maneja automáticamente la creación de directorios (data/raw/ y data/processed/) y cuenta con una barra de progreso visual para monitorear lotes grandes.

**Modo: Search**
Realiza la extracción inicial y filtra los perfiles. Utiliza el argumento --limit para establecer un tope máximo de leads a extraer (por defecto es 100).
```bash
python main.py --mode search --company "Nombre de la Empresa" --output data/raw/empresa.csv --limit 50
```
**Modo: Enrich**
Toma el CSV generado por el proceso de búsqueda e intenta obtener los correos verificados y teléfonos directos.
```bash
python main.py --mode enrich --input data/raw/empresa.csv --output data/processed/empresa_enriched.csv
```
## Estructura de Salida (Output)
Los archivos generados incluyen las siguientes columnas clave:

* full_name y title: Nombre y cargo estandarizado.
* seniority y departments: Nivel jerárquico y área de la empresa.
* email y email_status: Correo corporativo y su nivel de verificación (ej. verified).
* phone: Teléfono directo (se excluyen intencionalmente los teléfonos generales de recepción).
* contact_status: Validación interna del nivel de contacto encontrado.
* has_email_flag: Indicador nativo de Apollo sobre la existencia oculta de un email.

## Manejo de Errores Comunes
PermissionError (Errno 13): Si la terminal arroja un error de permisos al guardar, asegúrate de cerrar el archivo CSV en Excel u otro visor antes de ejecutar el comando.