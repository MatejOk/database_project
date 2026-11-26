import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

from catalog import CatalogItem, catalog_items
from models import Contractor, Location, Product
from quantities import QUANTITY, ceil_to_step, money, random_factor
from timeline import random_moment_between

PALLET_ZONE = "Strefa A"
SHELF_ZONE = "Strefa B"
CABLE_ZONE = "Strefa C"

HEAVY_ITEM_KG = Decimal("3")
NEW_PRODUCT_SHARE = 0.15
EDITED_PRODUCT_SHARE = 0.3
INACTIVE_LOCATION_SHARE = 0.05
PRIVATE_CLIENT_SHARE = 0.2
MARGIN = (1.18, 1.40)


@dataclass(frozen=True)
class ZoneLayout:
    name: str
    letter: str
    racks: int
    levels: int
    max_weight_kg: Decimal


ZONES = [
    ZoneLayout(PALLET_ZONE, "A", racks=6, levels=4, max_weight_kg=Decimal("1000")),
    ZoneLayout(SHELF_ZONE, "B", racks=10, levels=5, max_weight_kg=Decimal("200")),
    ZoneLayout(CABLE_ZONE, "C", racks=4, levels=3, max_weight_kg=Decimal("800")),
]

GROUND_LEVEL_BONUS = Decimal("1.5")

SUPPLIER_NAMES = [
    ("{} Dystrybucja Sp. z o.o.", "{}-dystrybucja"),
    ("Hurtownia Elektroniczna {}", "hurtownia-{}"),
    ("{} Electronics S.A.", "{}-electronics"),
    ("{} Import-Export Sp. z o.o.", "{}-import"),
    ("{} Kable i Przewody Sp.j.", "{}-kable"),
]

CLIENT_NAMES = [
    ("{} Software Sp. z o.o.", "{}-software"),
    ("Serwis Komputerowy {}", "serwis-{}"),
    ("Biuro Rachunkowe {}", "biuro-{}"),
    ("Kancelaria Prawna {} i Wspólnicy", "kancelaria-{}"),
    ("{} Instalacje Elektryczne", "{}-instalacje"),
    ("Sklep Komputerowy {}", "sklep-{}"),
    ("{} Logistyka Sp. z o.o.", "{}-logistyka"),
]

INTEGRATOR_NAMES = [
    ("{} Systemy IT Sp. z o.o.", "{}-systemy"),
    ("{} Integracja Sp.k.", "{}-integracja"),
    ("{} Technologie S.A.", "{}-technologie"),
]

MAILBOX = {"SUPPLIER": "sprzedaz", "CLIENT": "biuro", "BOTH": "kontakt"}
COMPANY_NAMES = {"SUPPLIER": SUPPLIER_NAMES, "CLIENT": CLIENT_NAMES, "BOTH": INTEGRATOR_NAMES}

POLISH_LETTERS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text.translate(POLISH_LETTERS)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def preferred_zone(item: CatalogItem) -> str:
    if item.unit == "m":
        return CABLE_ZONE
    if item.unit_weight_kg >= HEAVY_ITEM_KG:
        return PALLET_ZONE
    return SHELF_ZONE


def build_products(rng: Random, count: int, start: date, end: date) -> list[Product]:
    items = catalog_items()
    chosen = sorted(rng.sample(range(len(items)), count))
    products = []
    for product_id, index in enumerate(chosen, start=1):
        item = items[index]
        if rng.random() < NEW_PRODUCT_SHARE:
            created_at = random_moment_between(rng, start + timedelta(days=14), end - timedelta(days=30))
        else:
            created_at = random_moment_between(rng, start - timedelta(days=365), start - timedelta(days=1))
        updated_at = created_at
        if rng.random() < EDITED_PRODUCT_SHARE:
            updated_at = random_moment_between(rng, created_at.date() + timedelta(days=1), end)
        min_stock_step = Decimal("50") if item.unit == "m" else Decimal("1")
        products.append(Product(
            id=product_id,
            sku=item.sku,
            name=item.name,
            category=item.category,
            unit=item.unit,
            unit_weight_kg=item.unit_weight_kg,
            min_stock=ceil_to_step(Decimal(rng.randint(*item.min_stock_range)), min_stock_step),
            created_at=created_at,
            updated_at=updated_at,
            zone=preferred_zone(item),
            purchase_price=item.purchase_price,
            sale_price=money(item.purchase_price * random_factor(rng, MARGIN)),
        ))
    return products


def build_locations(rng: Random) -> list[Location]:
    locations = []
    for zone in ZONES:
        for rack in range(1, zone.racks + 1):
            for level in range(1, zone.levels + 1):
                max_weight = zone.max_weight_kg * (GROUND_LEVEL_BONUS if level == 1 else 1)
                locations.append(Location(
                    id=len(locations) + 1,
                    code=f"{zone.letter}-{rack:02}-{level:02}",
                    zone=zone.name,
                    max_weight_kg=max_weight.quantize(QUANTITY),
                    is_active=rng.random() >= INACTIVE_LOCATION_SHARE,
                ))
    return locations


def contractor_types(count: int) -> list[str]:
    suppliers = max(2, round(count * 0.2))
    integrators = round(count * 0.1)
    clients = count - suppliers - integrators
    return ["SUPPLIER"] * suppliers + ["BOTH"] * integrators + ["CLIENT"] * clients


def build_company(fake: Faker, rng: Random, contractor_id: int, contractor_type: str) -> Contractor:
    surname = fake.unique.last_name_male()
    name_pattern, domain_pattern = rng.choice(COMPANY_NAMES[contractor_type])
    return Contractor(
        id=contractor_id,
        name=name_pattern.format(surname),
        tax_id=fake.unique.company_vat(),
        contractor_type=contractor_type,
        email=f"{MAILBOX[contractor_type]}@{domain_pattern.format(slugify(surname))}.pl",
    )


def build_private_client(fake: Faker, rng: Random, contractor_id: int) -> Contractor:
    if rng.random() < 0.5:
        first_name, last_name = fake.first_name_male(), fake.last_name_male()
    else:
        first_name, last_name = fake.first_name_female(), fake.last_name_female()
    return Contractor(
        id=contractor_id,
        name=f"{first_name} {last_name}",
        tax_id=None,
        contractor_type="CLIENT",
        email=f"{slugify(first_name)}.{slugify(last_name)}{rng.randint(1, 99)}@{fake.free_email_domain()}",
    )


def build_contractors(rng: Random, fake: Faker, count: int) -> list[Contractor]:
    types = contractor_types(count)
    rng.shuffle(types)
    contractors = []
    for contractor_id, contractor_type in enumerate(types, start=1):
        if contractor_type == "CLIENT" and rng.random() < PRIVATE_CLIENT_SHARE:
            contractors.append(build_private_client(fake, rng, contractor_id))
        else:
            contractors.append(build_company(fake, rng, contractor_id, contractor_type))
    return contractors
