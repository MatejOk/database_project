import argparse
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ładuje wygenerowane dane do bazy SQLite i uruchamia kontrole spójności.")
    parser.add_argument("db", type=Path, help="plik bazy SQLite")
    parser.add_argument("--schema", type=Path, help="skrypt DDL; jego podanie tworzy nową bazę od zera")
    parser.add_argument("--seed", type=Path, default=HERE / "output" / "seed.sql", help="plik z danymi z generate.py")
    parser.add_argument("--verify", type=Path, default=HERE / "verify.sql", help="plik z kontrolami spójności")
    args = parser.parse_args()
    if args.schema and args.db.exists():
        parser.error(f"{args.db} już istnieje; usuń go albo pomiń --schema, żeby dograć dane do istniejącej bazy")
    return args


def main() -> None:
    args = parse_args()
    connection = sqlite3.connect(args.db)
    if args.schema:
        connection.executescript(args.schema.read_text(encoding="utf-8"))
    connection.executescript(args.seed.read_text(encoding="utf-8"))
    results = connection.execute(args.verify.read_text(encoding="utf-8")).fetchall()
    connection.close()

    for nr, rule, violations in results:
        status = "OK  " if violations == 0 else "BŁĄD"
        print(f"{status} {nr:>2}. {rule} (naruszenia: {violations})")
    raise SystemExit(0 if all(violations == 0 for *_, violations in results) else 1)


if __name__ == "__main__":
    main()
