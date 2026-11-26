# Generator danych testowych

Generuje spójne dane dla tabel `products`, `locations`, `contractors`, `stock_movements` i `stock_levels`.
Ten sam `--seed` zawsze daje identyczne dane.

## Instalacja

```bash
pip install -r requirements.txt
```

## Generowanie

```bash
python generate.py
```

Wynik trafia do `output/seed.sql`. Najważniejsze parametry (`python generate.py --help` pokazuje wszystkie):

| parametr          | domyślnie    | znaczenie                                  |
| ----------------- | ------------ | ------------------------------------------ |
| `--seed`          | `42`         | ziarno losowania                           |
| `--start`         | `2026-01-02` | pierwszy dzień ruchów                      |
| `--end`           | `2026-11-25` | ostatni dzień ruchów                       |
| `--products`      | cały katalog | liczba produktów (maks. 66)                |
| `--contractors`   | `40`         | liczba kontrahentów                        |
| `--docs-per-day`  | `6`          | średnia liczba dokumentów w dniu roboczym  |

## Ładowanie do SQLite i kontrola spójności

```bash
python load_sqlite.py magazyn.db --schema sciezka/do/schema.sql
```

Skrypt tworzy nową bazę ze schematu, ładuje `output/seed.sql` i uruchamia `verify.sql`.
Bez `--schema` dogrywa dane do istniejącej bazy. Kod wyjścia `0` oznacza, że wszystkie kontrole przeszły.

Z programem `sqlite3` to samo wygląda tak:

```bash
sqlite3 magazyn.db < sciezka/do/schema.sql
sqlite3 magazyn.db < output/seed.sql
sqlite3 -box magazyn.db < verify.sql
```
