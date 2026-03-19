import argparse

from src.apollo_leads.search import run_search
from src.apollo_leads.exporters import export_to_csv
from src.apollo_leads.enrich import run_enrichment


def main():
    parser = argparse.ArgumentParser(description="Apollo Leads CLI")

    parser.add_argument("--company", type=str, help="Empresa a buscar")
    parser.add_argument("--input", type=str, help="Archivo CSV de entrada")
    parser.add_argument("--output", type=str, default="data/raw/output.csv")

    parser.add_argument("--mode", type=str, choices=["search", "enrich"], required=True)

    args = parser.parse_args()

    if args.mode == "search":
        if not args.company:
            print("[ERROR] Debes usar --company en modo search")
            return

        records = run_search(args.company)
        export_to_csv(records, args.output)

        print(f"[OK] Search completo: {args.output}")

    elif args.mode == "enrich":
        if not args.input:
            print("[ERROR] Debes usar --input en modo enrich")
            return

        run_enrichment(args.input, args.output)


if __name__ == "__main__":
    main()