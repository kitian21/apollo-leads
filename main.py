from src.apollo_leads.search import run_search
# from src.apollo_leads.exporters import export_to_csv


def main() -> None:
    company = "HubSpot"
    output_file = "data/raw/hubspot_contacts.csv"

    records = run_search(company)
    # export_to_csv(records, output_file)

    print(f"[OK] Registros exportados: {len(records)}")
    print(f"[OK] Archivo: {output_file}")


if __name__ == "__main__":
    main()