WITH signed_movements AS (
    SELECT id, product_id, to_location_id AS location_id, quantity AS delta, created_at
    FROM stock_movements
    WHERE to_location_id IS NOT NULL
    UNION ALL
    SELECT id, product_id, from_location_id, -quantity, created_at
    FROM stock_movements
    WHERE from_location_id IS NOT NULL
),
balances AS (
    SELECT product_id, location_id, SUM(delta) AS quantity, MAX(created_at) AS last_change
    FROM signed_movements
    GROUP BY product_id, location_id
),
running_stock AS (
    SELECT SUM(delta) OVER (PARTITION BY product_id, location_id ORDER BY created_at, id) AS quantity
    FROM signed_movements
),
running_load AS (
    SELECT s.location_id,
           SUM(s.delta * p.unit_weight_kg) OVER (PARTITION BY s.location_id ORDER BY s.created_at, s.id) AS load_kg
    FROM signed_movements s
    JOIN products p ON p.id = s.product_id
),
documents AS (
    SELECT document_ref,
           COUNT(DISTINCT movement_type) AS types,
           COUNT(DISTINCT contractor_id) AS contractors,
           COUNT(DISTINCT created_at) AS moments
    FROM stock_movements
    GROUP BY document_ref
),
numbering AS (
    SELECT COUNT(DISTINCT document_ref) AS documents,
           MAX(CAST(substr(document_ref, length(movement_type) + 10) AS INTEGER)) AS last_number
    FROM stock_movements
    GROUP BY movement_type, strftime('%Y/%m', created_at)
),
checks AS (
    SELECT 1 AS nr, 'stock_levels = suma ruchów dla pary produkt-lokalizacja' AS rule, COUNT(*) AS violations
    FROM balances b
    LEFT JOIN stock_levels sl USING (product_id, location_id)
    WHERE round(b.quantity - COALESCE(sl.quantity, 0), 3) <> 0

    UNION ALL
    SELECT 2, 'stock_levels nie zawiera par bez ruchów', COUNT(*)
    FROM stock_levels sl
    LEFT JOIN balances b USING (product_id, location_id)
    WHERE b.product_id IS NULL

    UNION ALL
    SELECT 3, 'stan nigdy nie spada poniżej zera', COUNT(*)
    FROM running_stock
    WHERE round(quantity, 3) < 0

    UNION ALL
    SELECT 4, 'ładunek lokalizacji nigdy nie przekracza max_weight_kg', COUNT(*)
    FROM running_load r
    JOIN locations l ON l.id = r.location_id
    WHERE round(r.load_kg - l.max_weight_kg, 3) > 0

    UNION ALL
    SELECT 5, 'kolumny NULL zgodne z typem ruchu', COUNT(*)
    FROM stock_movements
    WHERE NOT (
           (movement_type = 'PZ' AND from_location_id IS NULL AND to_location_id IS NOT NULL
                                 AND contractor_id IS NOT NULL AND unit_price IS NOT NULL)
        OR (movement_type = 'WZ' AND from_location_id IS NOT NULL AND to_location_id IS NULL
                                 AND contractor_id IS NOT NULL AND unit_price IS NOT NULL)
        OR (movement_type = 'MM' AND from_location_id IS NOT NULL AND to_location_id IS NOT NULL
                                 AND from_location_id <> to_location_id
                                 AND contractor_id IS NULL AND unit_price IS NULL)
    )

    UNION ALL
    SELECT 6, 'PZ od dostawcy, WZ do klienta', COUNT(*)
    FROM stock_movements m
    JOIN contractors c ON c.id = m.contractor_id
    WHERE (m.movement_type = 'PZ' AND c.contractor_type NOT IN ('SUPPLIER', 'BOTH'))
       OR (m.movement_type = 'WZ' AND c.contractor_type NOT IN ('CLIENT', 'BOTH'))

    UNION ALL
    SELECT 7, 'numer dokumentu zgodny z typem i miesiącem ruchu', COUNT(*)
    FROM stock_movements
    WHERE document_ref NOT LIKE movement_type || '/' || strftime('%Y/%m', created_at) || '/%'

    UNION ALL
    SELECT 8, 'dokument ma jeden typ, jednego kontrahenta i jedną datę', COUNT(*)
    FROM documents
    WHERE types > 1 OR contractors > 1 OR moments > 1

    UNION ALL
    SELECT 9, 'numeracja dokumentów w miesiącu bez luk', COUNT(*)
    FROM numbering
    WHERE documents <> last_number

    UNION ALL
    SELECT 10, 'ruch nie wcześniej niż utworzenie produktu', COUNT(*)
    FROM stock_movements m
    JOIN products p ON p.id = m.product_id
    WHERE m.created_at < p.created_at

    UNION ALL
    SELECT 11, 'nieaktywne lokalizacje bez ruchów i stanów', COUNT(*)
    FROM locations l
    WHERE NOT l.is_active
      AND (EXISTS (SELECT 1 FROM stock_movements m WHERE l.id IN (m.from_location_id, m.to_location_id))
           OR EXISTS (SELECT 1 FROM stock_levels sl WHERE sl.location_id = l.id))

    UNION ALL
    SELECT 12, 'stock_levels.updated_at = data ostatniego ruchu', COUNT(*)
    FROM stock_levels sl
    JOIN balances b USING (product_id, location_id)
    WHERE sl.updated_at <> b.last_change

    UNION ALL
    SELECT 13, 'ilości dodatnie w ruchach i stanach', COUNT(*)
    FROM (
        SELECT quantity FROM stock_movements
        UNION ALL
        SELECT quantity FROM stock_levels
    ) q
    WHERE quantity <= 0

    UNION ALL
    SELECT 14, 'products.updated_at nie wcześniej niż created_at', COUNT(*)
    FROM products
    WHERE updated_at < created_at
)
SELECT nr, rule AS regula, violations AS naruszenia
FROM checks
ORDER BY nr;
