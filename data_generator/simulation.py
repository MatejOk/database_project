from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from random import Random
from typing import NamedTuple

from models import Contractor, Movement, Product
from quantities import ceil_to_step, handling_step, money, order_step, random_factor
from timeline import random_moment
from warehouse import Warehouse

DOCUMENT_TYPE_WEIGHTS = {"PZ": 12, "WZ": 73, "MM": 15}
TARGET_STOCK_FACTOR = (2.0, 3.5)
ORDER_SIZE_FACTOR = (0.05, 0.3)
PURCHASE_PRICE_SPREAD = (0.95, 1.05)
CLIENT_DISCOUNTS = [Decimal("0"), Decimal("0"), Decimal("0.03"), Decimal("0.05"), Decimal("0.08")]
OPENING_DOCUMENT_LINES = (6, 12)
RECEIPT_LINES = (3, 10)
ISSUE_LINES = (1, 5)
TRANSFER_LINES = (1, 3)


class Line(NamedTuple):
    product_id: int
    from_location_id: int | None
    to_location_id: int | None
    quantity: Decimal
    unit_price: Decimal | None


class Simulation:
    def __init__(self, rng: Random, products: list[Product], contractors: list[Contractor], warehouse: Warehouse, docs_per_day: float):
        self.rng = rng
        self.products = products
        self.warehouse = warehouse
        self.docs_per_day = docs_per_day
        self.suppliers = [c for c in contractors if c.contractor_type in ("SUPPLIER", "BOTH")]
        self.clients = [c for c in contractors if c.contractor_type in ("CLIENT", "BOTH")]
        self.client_activity = [rng.uniform(0.2, 1.0) ** 2 for _ in self.clients]
        self.movements: list[Movement] = []
        self.document_counters: dict[tuple[str, int, int], int] = defaultdict(int)

    def run(self, days: list[date]) -> list[Movement]:
        opening_day, *regular_days = days
        self.opening_balance(opening_day)
        handlers = {"PZ": self.receipt, "WZ": self.issue, "MM": self.transfer}
        for day in regular_days:
            for moment in self.document_moments(day):
                movement_type = self.rng.choices(list(DOCUMENT_TYPE_WEIGHTS), weights=DOCUMENT_TYPE_WEIGHTS.values())[0]
                handlers[movement_type](moment)
        return self.movements

    def document_moments(self, day: date) -> list[datetime]:
        count = max(0, round(self.rng.gauss(self.docs_per_day, self.docs_per_day * 0.3)))
        return sorted(random_moment(self.rng, day) for _ in range(count))

    def available_products(self, moment: datetime) -> list[Product]:
        return [product for product in self.products if product.created_at <= moment]

    def opening_balance(self, day: date) -> None:
        moments = sorted(random_moment(self.rng, day) for _ in range(len(self.products)))
        pending = self.available_products(moments[0])
        self.rng.shuffle(pending)
        for moment in moments:
            if not pending:
                break
            size = self.rng.randint(*OPENING_DOCUMENT_LINES)
            batch, pending = pending[:size], pending[size:]
            self.write_receipt(moment, batch)

    def receipt(self, moment: datetime) -> None:
        below_minimum = [
            product for product in self.available_products(moment)
            if self.warehouse.total(product.id) < product.min_stock
        ]
        if not below_minimum:
            return
        below_minimum.sort(key=lambda product: self.warehouse.total(product.id) / product.min_stock)
        self.write_receipt(moment, below_minimum[: self.rng.randint(*RECEIPT_LINES)])

    def write_receipt(self, moment: datetime, products: list[Product]) -> None:
        supplier = self.rng.choice(self.suppliers)
        lines = []
        for product in products:
            target = product.min_stock * random_factor(self.rng, TARGET_STOCK_FACTOR)
            missing = target - self.warehouse.total(product.id)
            quantity = ceil_to_step(missing, order_step(product.unit, product.purchase_price))
            price = money(product.purchase_price * random_factor(self.rng, PURCHASE_PRICE_SPREAD))
            for location_id, portion in self.warehouse.receive(product, quantity, moment):
                lines.append(Line(product.id, None, location_id, portion, price))
        self.add_document("PZ", moment, supplier.id, lines)

    def issue(self, moment: datetime) -> None:
        in_stock = [product for product in self.available_products(moment) if self.warehouse.total(product.id) > 0]
        if not in_stock:
            return
        client = self.rng.choices(self.clients, weights=self.client_activity)[0]
        discount = self.rng.choice(CLIENT_DISCOUNTS)
        lines = []
        for product in self.rng.sample(in_stock, min(len(in_stock), self.rng.randint(*ISSUE_LINES))):
            demand = ceil_to_step(product.min_stock * random_factor(self.rng, ORDER_SIZE_FACTOR), handling_step(product.unit))
            quantity = min(demand, self.warehouse.total(product.id))
            price = money(product.sale_price * (1 - discount))
            for location_id, portion in self.warehouse.issue(product, quantity, moment):
                lines.append(Line(product.id, location_id, None, portion, price))
        self.add_document("WZ", moment, client.id, lines)

    def transfer(self, moment: datetime) -> None:
        lines = []
        for _ in range(self.rng.randint(*TRANSFER_LINES)):
            plan = self.warehouse.relocation_plan()
            if plan is None:
                break
            product, source_id, quantity, targets = plan
            for target_id, portion in self.warehouse.transfer(product, source_id, quantity, targets, moment):
                lines.append(Line(product.id, source_id, target_id, portion, None))
        self.add_document("MM", moment, None, lines)

    def add_document(self, movement_type: str, moment: datetime, contractor_id: int | None, lines: list[Line]) -> None:
        if not lines:
            return
        counter_key = (movement_type, moment.year, moment.month)
        self.document_counters[counter_key] += 1
        document_ref = f"{movement_type}/{moment.year}/{moment.month:02}/{self.document_counters[counter_key]:03}"
        for line in lines:
            self.movements.append(Movement(
                id=len(self.movements) + 1,
                contractor_id=contractor_id,
                movement_type=movement_type,
                document_ref=document_ref,
                created_at=moment,
                **line._asdict(),
            ))
