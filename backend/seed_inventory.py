"""Sample sites and inventory for the program-level admin tools."""

SITES = [
    {"slug": "main-campus", "name": "Main Campus — W.A.I. HQ", "address": "1200 Industrial Pkwy", "capacity": 36},
    {"slug": "mobile-classroom", "name": "Camper-to-Classroom Mobile Unit", "address": "Off-grid mobile site", "capacity": 12},
    {"slug": "north-annex", "name": "North Annex Workshop", "address": "47 Conduit Way", "capacity": 18},
]

INVENTORY = [
    {"sku": "TLS-001", "name": "Klein Linesman Pliers 9\"", "category": "hand_tools", "quantity_total": 24, "site_slug": "main-campus"},
    {"sku": "TLS-002", "name": "Wire Strippers 10-22 AWG", "category": "hand_tools", "quantity_total": 30, "site_slug": "main-campus"},
    {"sku": "TLS-003", "name": "Torque Screwdriver (inch-lbs)", "category": "hand_tools", "quantity_total": 12, "site_slug": "main-campus"},
    {"sku": "TLS-004", "name": "Conduit Bender 1/2\" EMT", "category": "specialty", "quantity_total": 8, "site_slug": "north-annex"},
    {"sku": "TLS-005", "name": "Conduit Bender 3/4\" EMT", "category": "specialty", "quantity_total": 8, "site_slug": "north-annex"},
    {"sku": "TLS-006", "name": "Hydraulic Crimper 6-4/0", "category": "specialty", "quantity_total": 4, "site_slug": "main-campus"},
    {"sku": "MTR-001", "name": "Klein DMM (CAT III 600V)", "category": "meters", "quantity_total": 18, "site_slug": "main-campus"},
    {"sku": "MTR-002", "name": "Clamp-On AC Ammeter", "category": "meters", "quantity_total": 10, "site_slug": "main-campus"},
    {"sku": "MTR-003", "name": "Insulation Resistance Tester (Megger)", "category": "meters", "quantity_total": 4, "site_slug": "north-annex"},
    {"sku": "PPE-001", "name": "Class 0 Rubber Gloves (size 10)", "category": "ppe", "quantity_total": 40, "site_slug": "main-campus"},
    {"sku": "PPE-002", "name": "Arc-Rated Long Sleeve Shirt", "category": "ppe", "quantity_total": 30, "site_slug": "main-campus"},
    {"sku": "PPE-003", "name": "ANSI Z87.1 Safety Glasses", "category": "ppe", "quantity_total": 60, "site_slug": "main-campus"},
    {"sku": "SOL-001", "name": "400W PV Module (training)", "category": "solar", "quantity_total": 6, "site_slug": "mobile-classroom"},
    {"sku": "SOL-002", "name": "MPPT Charge Controller 60A", "category": "solar", "quantity_total": 4, "site_slug": "mobile-classroom"},
    {"sku": "SOL-003", "name": "48V LiFePO4 Battery (training)", "category": "solar", "quantity_total": 2, "site_slug": "mobile-classroom"},
]
