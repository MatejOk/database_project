from dataclasses import dataclass
from decimal import Decimal

ELECTRONICS = "Elektronika"
CABLES = "Kable"
ACCESSORIES = "Akcesoria"
OTHER = "Inne"


@dataclass(frozen=True)
class CatalogItem:
    sku: str
    name: str
    category: str
    unit: str
    unit_weight_kg: Decimal
    purchase_price: Decimal
    min_stock_range: tuple[int, int]


@dataclass(frozen=True)
class Family:
    category: str
    unit: str
    sku_prefix: str
    min_stock_range: tuple[int, int]
    models: list[tuple[str, str, str, str]]
    variants: list[tuple[str, str, str, str]]


SINGLE = [("", "", "1", "1")]

LAPTOP_CONFIGS = [
    ("I5-16-512", "i5 / 16 GB / 512 GB SSD", "1", "1"),
    ("I7-32-1TB", "i7 / 32 GB / 1 TB SSD", "1", "1.35"),
]

PATCH_LENGTHS = [
    ("1M", "1 m", "1", "1"),
    ("2M", "2 m", "1.6", "1.3"),
    ("3M", "3 m", "2.2", "1.6"),
    ("5M", "5 m", "3.4", "2.2"),
]

SHORT_LENGTHS = [
    ("1M", "1 m", "1", "1"),
    ("2M", "2 m", "1.6", "1.4"),
]

FAMILIES = [
    Family(ELECTRONICS, "szt.", "LAPTOP", (5, 15), [
        ("THINKPAD-T16", "Lenovo ThinkPad T16 Gen 2", "1.810", "4200"),
        ("THINKPAD-T14", "Lenovo ThinkPad T14 Gen 4", "1.380", "3900"),
        ("THINKPAD-X1", "Lenovo ThinkPad X1 Carbon Gen 11", "1.120", "6900"),
        ("LATITUDE-5440", "Dell Latitude 5440", "1.450", "3700"),
        ("LATITUDE-7440", "Dell Latitude 7440", "1.250", "5600"),
        ("ELITEBOOK-840-G10", "HP EliteBook 840 G10", "1.360", "4800"),
        ("PROBOOK-450-G10", "HP ProBook 450 G10", "1.790", "3100"),
    ], LAPTOP_CONFIGS),
    Family(ELECTRONICS, "szt.", "MONITOR", (5, 20), [
        ("DELL-P2423D", "Monitor Dell P2423D 23,8\" QHD", "5.550", "899"),
        ("DELL-U2724D", "Monitor Dell UltraSharp U2724D 27\"", "6.700", "1899"),
        ("LG-27UL500", "Monitor LG 27UL500-W 27\" 4K", "5.400", "1099"),
        ("SAMSUNG-S24C450", "Monitor Samsung S24C450 24\"", "3.900", "549"),
        ("IIYAMA-XU2493HS", "Monitor iiyama ProLite XU2493HS 24\"", "3.300", "469"),
    ], SINGLE),
    Family(ELECTRONICS, "szt.", "NET", (5, 20), [
        ("TPLINK-ARCHER-AX55", "Router TP-Link Archer AX55", "0.520", "289"),
        ("MIKROTIK-HAP-AX2", "Router MikroTik hAP ax2", "0.350", "349"),
        ("UBIQUITI-USW-LITE-8", "Switch Ubiquiti UniFi Switch Lite 8 PoE", "0.540", "459"),
        ("CISCO-CBS110-24T", "Switch Cisco CBS110-24T", "2.550", "699"),
        ("UBIQUITI-U6-LITE", "Punkt dostępowy Ubiquiti UniFi U6 Lite", "0.300", "399"),
    ], SINGLE),
    Family(ELECTRONICS, "szt.", "SSD", (10, 30), [
        ("SAMSUNG-990PRO-1TB", "Dysk SSD Samsung 990 PRO 1 TB NVMe", "0.009", "389"),
        ("KINGSTON-NV2-1TB", "Dysk SSD Kingston NV2 1 TB NVMe", "0.007", "219"),
        ("WD-SN580-500GB", "Dysk SSD WD Blue SN580 500 GB NVMe", "0.007", "159"),
        ("CRUCIAL-MX500-1TB", "Dysk SSD Crucial MX500 1 TB SATA", "0.045", "279"),
    ], SINGLE),
    Family(ELECTRONICS, "szt.", "DEV", (3, 10), [
        ("BROTHER-HL-L2350DW", "Drukarka laserowa Brother HL-L2350DW", "7.200", "499"),
        ("HP-LJ-M404DN", "Drukarka laserowa HP LaserJet Pro M404dn", "8.600", "1199"),
        ("APC-BX700", "Zasilacz UPS APC Back-UPS 700 VA", "5.500", "399"),
        ("EATON-5E850I", "Zasilacz UPS Eaton 5E 850i", "6.300", "449"),
    ], SINGLE),
    Family(CABLES, "m", "KAB", (500, 1500), [
        ("UTP-KAT6-CU", "Kabel U/UTP kat. 6 Cu", "0.040", "1.45"),
        ("FTP-KAT6A", "Kabel F/FTP kat. 6A", "0.065", "3.20"),
        ("YDY-3X2-5", "Przewód YDY 3x2,5 mm²", "0.125", "5.90"),
        ("H05VV-F-3X1", "Przewód H05VV-F 3x1 mm²", "0.075", "3.10"),
        ("RG6-COAX", "Kabel koncentryczny RG-6", "0.050", "1.80"),
        ("FIBER-SM-4J", "Kabel światłowodowy SM 4J zewnętrzny", "0.035", "2.60"),
    ], SINGLE),
    Family(CABLES, "szt.", "KAB", (30, 100), [
        ("PATCH-UTP-KAT6", "Patchcord U/UTP kat. 6", "0.040", "6.50"),
        ("HDMI-21", "Kabel HDMI 2.1", "0.090", "24.00"),
    ], PATCH_LENGTHS),
    Family(CABLES, "szt.", "KAB", (20, 60), [
        ("DP-14", "Kabel DisplayPort 1.4", "0.085", "29.00"),
        ("USBC-USBC-100W", "Kabel USB-C – USB-C 100 W", "0.045", "19.00"),
    ], SHORT_LENGTHS),
    Family(ACCESSORIES, "szt.", "ACC", (10, 40), [
        ("LOGI-MX-MASTER-3S", "Mysz Logitech MX Master 3S", "0.141", "339"),
        ("LOGI-M185", "Mysz bezprzewodowa Logitech M185", "0.075", "49"),
        ("LOGI-MX-KEYS-S", "Klawiatura Logitech MX Keys S", "0.810", "449"),
        ("DELL-KB216", "Klawiatura Dell KB216", "0.500", "59"),
        ("DELL-WD19S", "Stacja dokująca Dell WD19S 130 W", "1.400", "799"),
        ("LENOVO-USBC-DOCK-G2", "Stacja dokująca Lenovo ThinkPad USB-C Dock Gen 2", "1.200", "749"),
        ("JABRA-EVOLVE2-40", "Słuchawki Jabra Evolve2 40 USB-C", "0.140", "389"),
        ("LOGI-C920", "Kamera internetowa Logitech C920 HD Pro", "0.162", "289"),
        ("BAG-15-6", "Torba na laptopa 15,6\"", "0.650", "119"),
        ("CHARGER-USBC-65W", "Ładowarka sieciowa USB-C 65 W GaN", "0.120", "129"),
    ], SINGLE),
    Family(OTHER, "kg", "MAT", (10, 40), [
        ("CABLE-TIES-200", "Opaski zaciskowe 200x4,8 mm (luzem)", "1.000", "38.00"),
        ("SOLDER-SN60-08", "Cyna lutownicza Sn60Pb40 0,8 mm", "1.000", "189.00"),
        ("STRETCH-FILM-23", "Folia stretch transparentna 23 µm", "1.000", "9.50"),
    ], SINGLE),
    Family(OTHER, "szt.", "MAT", (20, 60), [
        ("ARCTIC-MX4-4G", "Pasta termoprzewodząca Arctic MX-4 4 g", "0.010", "19.00"),
        ("AIR-DUSTER-400", "Sprężone powietrze 400 ml", "0.290", "14.00"),
        ("SCREEN-WIPES-100", "Chusteczki do czyszczenia ekranów (100 szt.)", "0.180", "12.00"),
    ], SINGLE),
]


def catalog_items() -> list[CatalogItem]:
    items = []
    for family in FAMILIES:
        for model_sku, model_name, weight, price in family.models:
            for variant_sku, variant_name, weight_factor, price_factor in family.variants:
                items.append(CatalogItem(
                    sku="-".join(part for part in (family.sku_prefix, model_sku, variant_sku) if part),
                    name=f"{model_name} {variant_name}".strip(),
                    category=family.category,
                    unit=family.unit,
                    unit_weight_kg=(Decimal(weight) * Decimal(weight_factor)).quantize(Decimal("0.001")),
                    purchase_price=(Decimal(price) * Decimal(price_factor)).quantize(Decimal("0.01")),
                    min_stock_range=family.min_stock_range,
                ))
    return items
