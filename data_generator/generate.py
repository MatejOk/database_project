import argparse
from datetime import date, timedelta
from pathlib import Path
from random import Random

from faker import Faker

from catalog import catalog_items
from master_data import build_contractors, build_locations, build_products
from simulation import Simulation
from sql_writer import write_sql
from timeline import working_days
from warehouse import Warehouse

MIN_PERIOD = timedelta(days=60)
MIN_CONTRACTORS = 4


def parse_args() -> argparse.Namespace:
    catalog_size = len(catalog_items())
    parser = argparse.ArgumentParser(description="Generator spójnych danych testowych dla bazy magazynowej.")
    parser.add_argument("--seed", type=int, default=42, help="ziarno losowania; ten sam seed daje te same dane")
    parser.add_argument("--start", type=date.fromisoformat, default=date(2026, 1, 2), help="pierwszy dzień ruchów (RRRR-MM-DD)")
    parser.add_argument("--end", type=date.fromisoformat, default=date(2026, 11, 25), help="ostatni dzień ruchów (RRRR-MM-DD)")
    parser.add_argument("--products", type=int, default=catalog_size, help=f"liczba produktów (1-{catalog_size})")
    parser.add_argument("--contractors", type=int, default=40, help=f"liczba kontrahentów (min. {MIN_CONTRACTORS})")
    parser.add_argument("--docs-per-day", type=float, default=6, help="średnia liczba dokumentów w dniu roboczym")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output" / "seed.sql")
    args = parser.parse_args()

    if args.end - args.start < MIN_PERIOD:
        parser.error(f"okres musi mieć co najmniej {MIN_PERIOD.days} dni")
    if not 1 <= args.products <= catalog_size:
        parser.error(f"--products musi być w zakresie 1-{catalog_size}")
    if args.contractors < MIN_CONTRACTORS:
        parser.error(f"--contractors musi wynosić co najmniej {MIN_CONTRACTORS}")
    if args.docs_per_day <= 0:
        parser.error("--docs-per-day musi być dodatnie")
    return args


def main() -> None:
    args = parse_args()
    rng = Random(args.seed)
    fake = Faker("pl_PL")
    fake.seed_instance(args.seed)

    products = build_products(rng, args.products, args.start, args.end)
    locations = build_locations(rng)
    contractors = build_contractors(rng, fake, args.contractors)
    warehouse = Warehouse(rng, products, locations)
    movements = Simulation(rng, products, contractors, warehouse, args.docs_per_day).run(working_days(args.start, args.end))
    stock_levels = warehouse.stock_levels()

    tables = {
        "products": products,
        "locations": locations,
        "contractors": contractors,
        "stock_movements": movements,
        "stock_levels": stock_levels,
    }
    write_sql(args.output, tables, f"seed={args.seed}, okres {args.start} – {args.end}")

    print(f"Zapisano {args.output}")
    for table, rows in tables.items():
        print(f"  {table:<16} {len(rows):>6} wierszy")
    print(f"  {'dokumenty':<16} {len({m.document_ref for m in movements}):>6}")


if __name__ == "__main__":
    main()
