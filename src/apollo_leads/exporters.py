import csv
from typing import Dict, List
from .config import OUTPUT_FIELDS


def export_to_csv(records: List[Dict], output_file: str) -> None:
    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, delimiter=";")
        writer.writeheader()

        for record in records:
            writer.writerow({field: record.get(field) for field in OUTPUT_FIELDS})