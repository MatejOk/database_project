from datetime import datetime
from decimal import Decimal
from pathlib import Path

COLUMNS = {
    "products": ("id", "sku", "name", "category", "unit", "unit_weight_kg", "min_stock", "created_at", "updated_at"),
    "locations": ("id", "code", "zone", "max_weight_kg", "is_active"),
    "contractors": ("id", "name", "tax_id", "contractor_type", "email"),
    "stock_movements": (
        "id", "product_id", "contractor_id", "from_location_id", "to_location_id",
        "movement_type", "quantity", "unit_price", "document_ref", "created_at",
    ),
    "stock_levels": ("product_id", "location_id", "quantity", "updated_at"),
}

BATCH_SIZE = 500


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return f"'{value:%Y-%m-%d %H:%M:%S}'"
    return "'" + str(value).replace("'", "''") + "'"


def insert_statements(table: str, rows: list) -> list[str]:
    columns = COLUMNS[table]
    statements = []
    for offset in range(0, len(rows), BATCH_SIZE):
        values = ",\n".join(
            "  (" + ", ".join(sql_literal(getattr(row, column)) for column in columns) + ")"
            for row in rows[offset:offset + BATCH_SIZE]
        )
        statements.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n{values};\n")
    return statements


def write_sql(path: Path, tables: dict[str, list], header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        file.write(f"-- {header}\n\nPRAGMA foreign_keys = ON;\n\nBEGIN;\n\n")
        for table, rows in tables.items():
            for statement in insert_statements(table, rows):
                file.write(statement + "\n")
        file.write("COMMIT;\n")
