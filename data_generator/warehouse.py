from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from random import Random

from models import Location, Product, StockLevel
from quantities import floor_to_step, handling_step, random_factor

Part = tuple[int, Decimal]

MAX_PLACES_IN_ZONE = 2
REMNANT_SHARE = Decimal("0.25")
SPLIT_SHARE = (0.3, 0.5)


class Warehouse:
    def __init__(self, rng: Random, products: list[Product], locations: list[Location]):
        self.rng = rng
        self.products = {product.id: product for product in products}
        self.locations = [location for location in locations if location.is_active]
        self.zone_of = {location.id: location.zone for location in self.locations}
        self.capacity = {location.id: location.max_weight_kg for location in self.locations}
        self.load: dict[int, Decimal] = defaultdict(Decimal)
        self.stock: dict[int, dict[int, Decimal]] = defaultdict(dict)
        self.last_change: dict[tuple[int, int], datetime] = {}

    def total(self, product_id: int) -> Decimal:
        return sum(self.stock[product_id].values(), Decimal(0))

    def units_that_fit(self, product: Product, location_id: int) -> Decimal:
        free_kg = self.capacity[location_id] - self.load[location_id]
        return floor_to_step(free_kg / product.unit_weight_kg, handling_step(product.unit))

    def zone_targets(self, product: Product, exclude: int | None = None) -> list[int]:
        places = self.stock[product.id]
        holding = sorted(
            (location_id for location_id in places if location_id != exclude and self.zone_of[location_id] == product.zone),
            key=places.get,
            reverse=True,
        )
        others = [
            location.id for location in self.locations
            if location.zone == product.zone and location.id != exclude and location.id not in places
        ]
        self.rng.shuffle(others)
        return holding + others

    def overflow_targets(self, product: Product) -> list[int]:
        targets = [location.id for location in self.locations if location.zone != product.zone]
        self.rng.shuffle(targets)
        return targets

    def receive(self, product: Product, quantity: Decimal, at: datetime) -> list[Part]:
        parts = []
        remaining = quantity
        for location_id in self.zone_targets(product) + self.overflow_targets(product):
            if remaining <= 0:
                break
            portion = min(remaining, self.units_that_fit(product, location_id))
            if portion > 0:
                self._change(product, location_id, portion, at)
                parts.append((location_id, portion))
                remaining -= portion
        return parts

    def issue(self, product: Product, quantity: Decimal, at: datetime) -> list[Part]:
        parts = []
        remaining = quantity
        for location_id, available in sorted(self.stock[product.id].items(), key=lambda place: place[1]):
            if remaining <= 0:
                break
            portion = min(remaining, available)
            self._change(product, location_id, -portion, at)
            parts.append((location_id, portion))
            remaining -= portion
        return parts

    def transfer(self, product: Product, source_id: int, quantity: Decimal, targets: list[int], at: datetime) -> list[Part]:
        parts = []
        remaining = quantity
        for target_id in targets:
            if remaining <= 0:
                break
            portion = min(remaining, self.units_that_fit(product, target_id))
            if portion > 0:
                self._change(product, source_id, -portion, at)
                self._change(product, target_id, portion, at)
                parts.append((target_id, portion))
                remaining -= portion
        return parts

    def relocation_plan(self) -> tuple[Product, int, Decimal, list[int]] | None:
        for product, source_id, quantity, targets in self._relocation_candidates():
            if any(self.units_that_fit(product, target_id) > 0 for target_id in targets):
                return product, source_id, quantity, targets
        return None

    def stock_levels(self) -> list[StockLevel]:
        return [
            StockLevel(product_id, location_id, quantity, self.last_change[(product_id, location_id)])
            for product_id in sorted(self.stock)
            for location_id, quantity in sorted(self.stock[product_id].items())
        ]

    def _relocation_candidates(self):
        misplaced, fragmented, splits = [], [], []
        for product_id, places in self.stock.items():
            product = self.products[product_id]
            in_zone = sorted((loc for loc in places if self.zone_of[loc] == product.zone), key=places.get)
            for location_id in places:
                if self.zone_of[location_id] != product.zone:
                    misplaced.append((product, location_id, places[location_id], self.zone_targets(product, exclude=location_id)))
            if self._is_fragmented(places, in_zone):
                smallest, *larger = in_zone
                fragmented.append((product, smallest, places[smallest], larger[::-1]))
            elif len(in_zone) == 1:
                location_id = in_zone[0]
                part = floor_to_step(places[location_id] * random_factor(self.rng, SPLIT_SHARE), handling_step(product.unit))
                if 0 < part < places[location_id]:
                    splits.append((product, location_id, part, self.zone_targets(product, exclude=location_id)))
        for group in (misplaced, fragmented, splits):
            self.rng.shuffle(group)
            yield from group

    @staticmethod
    def _is_fragmented(places: dict[int, Decimal], in_zone: list[int]) -> bool:
        if len(in_zone) > MAX_PLACES_IN_ZONE:
            return True
        if len(in_zone) < 2:
            return False
        total = sum(places[location_id] for location_id in in_zone)
        return places[in_zone[0]] < total * REMNANT_SHARE

    def _change(self, product: Product, location_id: int, delta: Decimal, at: datetime) -> None:
        places = self.stock[product.id]
        new_quantity = places.get(location_id, Decimal(0)) + delta
        new_load = self.load[location_id] + delta * product.unit_weight_kg
        if new_quantity < 0:
            raise ValueError(f"Ujemny stan produktu {product.sku} na lokalizacji {location_id}")
        if new_load > self.capacity[location_id]:
            raise ValueError(f"Przekroczona nośność lokalizacji {location_id}")
        self.load[location_id] = new_load
        if new_quantity == 0:
            del places[location_id]
        else:
            places[location_id] = new_quantity
        self.last_change[(product.id, location_id)] = at
