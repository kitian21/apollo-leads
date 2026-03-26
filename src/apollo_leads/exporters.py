import csv
import sys
from pathlib import Path
from typing import Dict, List
from .config import OUTPUT_FIELDS


def export_to_csv(records: List[Dict], output_file: str) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, delimiter=";")
            writer.writeheader()

            for record in records:
                writer.writerow({field: record.get(field) for field in OUTPUT_FIELDS})
                
    except PermissionError:
        print(f"\n[ERROR] Acceso denegado al guardar en '{output_path}'.")
        print("💡 Consejo: Asegúrate de no tener el archivo CSV abierto en Excel.")
        print("Ciérralo e inténtalo de nuevo.\n")
        sys.exit(1)