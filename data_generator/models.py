from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Product:
    id: int
    sku: str
    name: str
    category: str
    unit: str
    unit_weight_kg: Decimal
    min_stock: Decimal
    created_at: datetime
    updated_at: datetime
    zone: str
    purchase_price: Decimal
    sale_price: Decimal


@dataclass
class Location:
    id: int
    code: str
    zone: str
    max_weight_kg: Decimal
    is_active: bool


@dataclass
class Contractor:
    id: int
    name: str
    tax_id: str | None
    contractor_type: str
    email: str


@dataclass
class Movement:
    id: int
    product_id: int
    contractor_id: int | None
    from_location_id: int | None
    to_location_id: int | None
    movement_type: str
    quantity: Decimal
    unit_price: Decimal | None
    document_ref: str
    created_at: datetime


@dataclass
class StockLevel:
    product_id: int
    location_id: int
    quantity: Decimal
    updated_at: datetime
