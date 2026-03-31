import argparse
import csv
from pathlib import Path
from src.apollo_leads.search import run_search
from src.apollo_leads.enrich import run_enrichment

def save_csv(records, output_file):
    if not records:
        return
    
    # Crea la carpeta si no existe
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(records[0].keys())
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(records)

def main():
    parser = argparse.ArgumentParser(description="Apollo Leads B2B Extractor")
    parser.add_argument("--mode", choices=["search", "enrich"], required=True, help="Modo de ejecución")
    
    # Argumentos para Search
    parser.add_argument("--company", type=str, help="Nombre de una empresa individual para buscar")
    parser.add_argument("--file", type=str, help="Ruta a un archivo .txt con la lista de empresas")
    parser.add_argument("--limit", type=int, default=100, help="Límite de leads por empresa")
    
    # Argumentos para Enrich y outputs
    parser.add_argument("--input", type=str, help="Archivo o carpeta CSV de entrada (solo para enrich)")
    parser.add_argument("--output", type=str, help="Archivo CSV de salida")

    args = parser.parse_args()

    if args.mode == "search":
        # MODO MASIVO: Búsqueda desde un archivo .txt
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    # Lee las líneas, quita espacios extra y omite líneas en blanco
                    empresas = [line.strip() for line in f if line.strip()]
                
                print(f"[INFO] Iniciando búsqueda masiva para {len(empresas)} empresas.")
                
                for empresa in empresas:
                    print(f"\n{'='*40}")
                    print(f"🚀 Procesando: {empresa}")
                    print(f"{'='*40}")
                    
                    records = run_search(company_input=empresa, limit=args.limit)
                    
                    if records:
                        # Genera un nombre de archivo limpio (ej: "Constructora_Cerro.csv")
                        nombre_limpio = empresa.replace(" ", "_").replace(",", "").replace(".", "")
                        out_path = f"data/raw/{nombre_limpio}.csv"
                        save_csv(records, out_path)
                        print(f"[OK] {len(records)} leads guardados en {out_path}")
                    else:
                        print(f"[WARNING] No se extrajeron leads para {empresa}.")
            
            except FileNotFoundError:
                print(f"[ERROR] No se encontró el archivo: {args.file}")

        # MODO INDIVIDUAL: Búsqueda de una sola empresa
        elif args.company and args.output:
            records = run_search(company_input=args.company, limit=args.limit)
            save_csv(records, args.output)
            print(f"\n[OK] Guardado en {args.output}")
        else:
            print("[ERROR] Para buscar necesitas proveer --company y --output, o utilizar --file")

    elif args.mode == "enrich":
        if not args.input or not args.output:
            print("[ERROR] El modo enrich requiere --input y --output")
            return
        run_enrichment(args.input, args.output)

if __name__ == "__main__":
    main()