"""
seed_construction_pm.py — Populate the construction_pm MongoDB collections
with 4 progressive seed projects modeling increasing commercial electrical
complexity.

Usage:
    cd backend
    MONGO_URL=mongodb://localhost:27017 python seed_construction_pm.py

Connects directly to MongoDB (bypassing FastAPI auth) and inserts:
  * construction_division26  — CSI Division 26 catalog items
  * construction_projects    — 4 seed projects (retail → industrial)
  * construction_estimate_versions — bid snapshots per project
  * construction_daily_logs  — field productivity entries (drives benchmarks)
  * construction_benchmarks  — empirical labor rates (recalculated from logs)
  * construction_blueprints  — uploaded plan-set metadata

All money in cents where applicable; labor in hours; multipliers are dimensionless.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

DB_NAME = os.environ.get("MONGO_DB_NAME", "morehelp_center")

# ── CSI Division 26 catalog ───────────────────────────────────────────────────
# (item_id, csi_code, description, uom, default_material_cost, default_labor_hours)
DIVISION26_CATALOG = [
    # 26 05 33 — Conduit, Raceway, and Boxes
    ("26-05-33-001", "26 05 33", "3/4\" EMT Conduit (10ft stick)", "lf", 2.85, 0.05),
    ("26-05-33-002", "26 05 33", "1\" EMT Conduit (10ft stick)", "lf", 3.40, 0.06),
    ("26-05-33-003", "26 05 33", "4\" Square Steel Box (4-11/16\" deep)", "ea", 4.20, 0.25),
    ("26-05-33-004", "26 05 33", "EMT Compression Connector 3/4\"", "ea", 1.10, 0.08),
    ("26-05-33-005", "26 05 33", "EMT Compression Coupling 3/4\"", "ea", 0.95, 0.06),
    ("26-05-33-006", "26 05 33", "4\" Octagon Box (device box)", "ea", 2.95, 0.20),
    # 26 05 19 — Conductors and Cables
    ("26-05-19-001", "26 05 19", "12 AWG THHN Copper (solid)", "lf", 0.42, 0.015),
    ("26-05-19-002", "26 05 19", "12 AWG THHN Copper (stranded)", "lf", 0.45, 0.018),
    ("26-05-19-003", "26 05 19", "10 AWG THHN Copper", "lf", 0.68, 0.020),
    ("26-05-19-004", "26 05 19", "1/0 AWG THHN Copper", "lf", 2.40, 0.040),
    ("26-05-19-005", "26 05 19", "4/0 AWG THHN Copper", "lf", 4.95, 0.075),
    # 26 24 16 — Switchboards, Panels, and Disconnects
    ("26-24-16-001", "26 24 16", "100A 120/208V Main Lugs Panel (20-circuit)", "ea", 850.00, 4.00),
    ("26-24-16-002", "26 24 16", "225A 120/208V Main Breaker Panel (42-circuit)", "ea", 1850.00, 8.00),
    ("26-24-16-003", "26 24 16", "1200A Main Distribution Switchboard", "ea", 24000.00, 40.00),
    ("26-24-16-004", "26 24 16", "30A NEMA 3R Disconnect Switch", "ea", 145.00, 1.50),
    ("26-24-16-005", "26 24 16", "60A Fused Disconnect Switch", "ea", 220.00, 2.00),
    # 26 09 23 — Lighting Control Devices
    ("26-09-23-001", "26 09 23", "0-10V Dimmer Wall Switch", "ea", 38.00, 0.50),
    ("26-09-23-002", "26 09 23", "Occupancy Sensor Ceiling Mount", "ea", 62.00, 0.75),
    ("26-09-23-003", "26 09 23", "Panel-Mounted Lighting Control Relay", "ea", 185.00, 1.25),
    # 26 27 26 — Wiring Devices
    ("26-27-26-001", "26 27 26", "20A Duplex Receptacle (Commercial Grade)", "ea", 3.20, 0.30),
    ("26-27-26-002", "26 27 26", "20A GFCI Receptacle", "ea", 18.50, 0.45),
    ("26-27-26-003", "26 27 26", "Single Pole 20A Switch", "ea", 2.80, 0.25),
    # 26 32 13 — Generator Backup & ATS
    ("26-32-13-001", "26 32 13", "200A Automatic Transfer Switch (3-pole)", "ea", 2400.00, 6.00),
    ("26-32-13-002", "26 32 13", "40kW Diesel Generator (Skid-mounted)", "ea", 18500.00, 16.00),
    # 26 27 13 — Metering & Isolated Grounds
    ("26-27-13-001", "26 27 13", "Isolated Ground Duplex Receptacle", "ea", 24.00, 0.35),
    ("26-27-13-002", "26 27 13", "Revenue Grade kWh Meter (3-phase)", "ea", 480.00, 1.75),
    # 26 28 16 — Enclosed Disconnects
    ("26-28-16-001", "26 28-16", "30A Enclosed Disconnect (NEMA 4X)", "ea", 165.00, 1.75),
    ("26-28-16-002", "26 28-16", "100A Enclosed Disconnect (NEMA 3R)", "ea", 320.00, 2.50),
]

# ── Seed project definitions ──────────────────────────────────────────────────
# Each project: core fields, crew blend, line items [(item_id, qty, multipliers)], blueprints
SEED_PROJECTS = [
    {
        "job_number": "#2026-E-101",
        "client_name": "Downtown Commercial Strip — Retail TI",
        "site_address": "1234 N Franklin St, Tampa, FL 33602",
        "contract_value": 45000,
        "current_phase": "pre_con",
        "crew_blend": {
            "foreman_ratio": 0.05,
            "journeyman_ratio": 0.75,
            "apprentice_ratio": 0.20,
            "blended_hourly_rate": 85.00,
            "fringe_burden": 12.00,
        },
        "multipliers": [1.00],
        "line_items": [
            ("26-05-33-001", 480, [1.00]),   # 3/4 EMT — 480 lf
            ("26-05-33-003", 12, [1.00]),   # 4\" Square Box — 12 ea
            ("26-05-33-004", 24, [1.00]),   # EMT Connector 3/4 — 24 ea
            ("26-05-33-005", 36, [1.00]),   # EMT Coupling 3/4 — 36 ea
            ("26-05-33-006", 24, [1.00]),   # Octagon Box — 24 ea
            ("26-05-19-001", 1440, [1.00]), # 12 AWG THHN — 1440 lf
            ("26-24-16-001", 1, [1.00]),    # 100A Panel — 1 ea
            ("26-27-26-001", 24, [1.00]),   # Duplex Receptacle — 24 ea
            ("26-27-26-003", 8, [1.00]),    # Single Pole Switch — 8 ea
        ],
        "blueprints": [
            ("E-101", "https://morehelp.center/storage/seeds/E-101_retail_floor_plan.pdf", 1.0,
             {"layers": ["branch_power", "lighting", "devices"], "scale": "1/8\" = 1'-0\""}),
        ],
    },
    {
        "job_number": "#2026-E-102",
        "client_name": "Westshore Office Park — Floor 3 Refurb",
        "site_address": "4560 W Kennedy Blvd, Tampa, FL 33609",
        "contract_value": 185000,
        "current_phase": "construction",
        "crew_blend": {
            "foreman_ratio": 0.10,
            "journeyman_ratio": 0.70,
            "apprentice_ratio": 0.20,
            "blended_hourly_rate": 92.00,
            "fringe_burden": 14.00,
        },
        "multipliers": [1.15, 1.10],  # occupied facility + overhead scaffold
        "line_items": [
            ("26-05-33-002", 960, [1.15, 1.10]),   # 1\" EMT — 960 lf
            ("26-05-33-004", 64, [1.15, 1.10]),    # EMT Connector — 64 ea
            ("26-05-33-005", 96, [1.15, 1.10]),    # EMT Coupling — 96 ea
            ("26-05-19-002", 2880, [1.15, 1.10]),  # 12 AWG Stranded — 2880 lf
            ("26-05-19-003", 480, [1.15, 1.10]),   # 10 AWG THHN — 480 lf
            ("26-09-23-001", 16, [1.15, 1.10]),    # 0-10V Dimmer — 16 ea
            ("26-09-23-002", 12, [1.15, 1.10]),    # Occupancy Sensor — 12 ea
            ("26-24-16-002", 1, [1.15, 1.10]),     # 225A Panel — 1 ea
            ("26-27-26-001", 48, [1.15, 1.10]),    # Duplex Receptacle — 48 ea
            ("26-27-26-002", 8, [1.15, 1.10]),     # GFCI Receptacle — 8 ea
            ("26-27-26-003", 24, [1.15, 1.10]),    # Single Pole Switch — 24 ea
        ],
        "blueprints": [
            ("E-201", "https://morehelp.center/storage/seeds/E-201_office_floor3.pdf", 1.0,
             {"layers": ["branch_power", "lighting_controls", "devices"], "scale": "1/8\" = 1'-0\""}),
            ("E-202", "https://morehelp.center/storage/seeds/E-202_office_lighting.pdf", 1.0,
             {"layers": ["lighting_zones", "controls"], "scale": "1/8\" = 1'-0\""}),
        ],
    },
    {
        "job_number": "#2026-E-103",
        "client_name": "Bay Pines Medical Plaza — Core & Shell",
        "site_address": "789 4th Ave N, St. Petersburg, FL 33701",
        "contract_value": 420000,
        "current_phase": "pre_con",
        "crew_blend": {
            "foreman_ratio": 0.12,
            "journeyman_ratio": 0.68,
            "apprentice_ratio": 0.20,
            "blended_hourly_rate": 98.00,
            "fringe_burden": 16.00,
        },
        "multipliers": [1.20, 1.15],  # ICRA + ceiling congestion
        "line_items": [
            ("26-05-33-002", 720, [1.20, 1.15]),    # 1\" EMT — 720 lf
            ("26-05-33-001", 1200, [1.20, 1.15]),   # 3/4 EMT — 1200 lf
            ("26-05-19-003", 2160, [1.20, 1.15]),   # 10 AWG THHN — 2160 lf
            ("26-05-19-004", 320, [1.20, 1.15]),    # 1/0 AWG THHN — 320 lf
            ("26-24-16-002", 2, [1.20, 1.15]),      # 225A Panel — 2 ea
            ("26-32-13-001", 1, [1.20, 1.15]),      # 200A ATS — 1 ea
            ("26-27-13-001", 32, [1.20, 1.15]),     # Isolated Ground Receptacle — 32 ea
            ("26-27-13-002", 4, [1.20, 1.15]),      # kWh Meter — 4 ea
            ("26-27-26-001", 64, [1.20, 1.15]),     # Duplex Receptacle — 64 ea
        ],
        "blueprints": [
            ("E-301", "https://morehelp.center/storage/seeds/E-301_medical_floor_plan.pdf", 1.0,
             {"layers": ["isolated_ground", "emergency", "hvac_interlock"], "scale": "1/8\" = 1'-0\""}),
            ("E-302", "https://morehelp.center/storage/seeds/E-302_medical_riser.pdf", 1.0,
             {"layers": ["feeder", "generator_tie_in"], "scale": "3/16\" = 1'-0\""}),
        ],
    },
    {
        "job_number": "#2026-E-042",
        "client_name": "Port Tampa Industrial Warehouse — Switchgear Retrofit",
        "site_address": "1102 Maritime Blvd, Tampa, FL 33605",
        "contract_value": 950000,
        "current_phase": "construction",
        "crew_blend": {
            "foreman_ratio": 0.15,
            "journeyman_ratio": 0.60,
            "apprentice_ratio": 0.25,
            "blended_hourly_rate": 105.00,
            "fringe_burden": 18.00,
        },
        "multipliers": [1.30, 1.25, 1.40],  # LOTO + crane + compressed window
        "line_items": [
            ("26-24-16-003", 1, [1.30, 1.25, 1.40]),  # 1200A Switchboard — 1 ea
            ("26-05-19-004", 400, [1.30, 1.25, 1.40]), # 1/0 AWG Parallel — 400 lf
            ("26-05-19-005", 120, [1.30, 1.25, 1.40]), # 4/0 AWG Parallel — 120 lf
            ("26-28-16-002", 6, [1.30, 1.25, 1.40]),   # 100A Enclosed Disconnect — 6 ea
            ("26-24-16-004", 4, [1.30, 1.25, 1.40]),   # 30A Disconnect — 4 ea
        ],
        "blueprints": [
            ("E-401", "https://morehelp.center/storage/seeds/E-401_switchgear_one_line.pdf", 1.0,
             {"layers": ["main_distribution", "feeders", "disconnects"], "scale": "1/4\" = 1'-0\""}),
            ("E-402", "https://morehelp.center/storage/seeds/E-402_site_plan.pdf", 1.0,
             {"layers": ["generator_tie_in", "utility_outage"], "scale": "1\" = 20'-0\""}),
        ],
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _calc_extended(material_cost, labor_hours, qty, multipliers, blended_rate, fringe):
    stack = 1.0
    for m in multipliers:
        stack *= max(m, 0.0)
    effective_labor_hours = labor_hours * stack
    extended_material = round(material_cost * qty, 2)
    extended_labor = round(effective_labor_hours * blended_rate * qty, 2)
    fringe_cost = round(fringe * qty, 2)
    direct_cost = round(extended_material + extended_labor + fringe_cost, 2)
    return {
        "extended_material": extended_material,
        "extended_labor": extended_labor,
        "fringe_cost": fringe_cost,
        "direct_cost": direct_cost,
        "effective_labor_hours_per_unit": round(effective_labor_hours, 4),
    }


async def seed():
    mongo_url = os.environ.get("MONGO_URL")
    if not mongo_url:
        print("ERROR: MONGO_URL environment variable is required")
        sys.exit(1)

    client = AsyncIOMotorClient(mongo_url)
    db = client[DB_NAME]

    print(f"Connected to MongoDB database: {DB_NAME}")

    # ───── Clear existing construction_pm data (idempotent re-seed) ─────
    for coll in [
        "construction_projects",
        "construction_division26",
        "construction_estimate_versions",
        "construction_daily_logs",
        "construction_benchmarks",
        "construction_blueprints",
    ]:
        await db[coll].delete_many({})
    print("Cleared existing construction_pm collections.")

    # ───── Division 26 catalog ─────
    now = _now()
    div_docs = []
    for item_id, csi_code, description, uom, mat_cost, labor_hrs in DIVISION26_CATALOG:
        div_docs.append({
            "item_id": item_id,
            "csi_code": csi_code,
            "description": description,
            "uom": uom,
            "default_material_cost": mat_cost,
            "default_labor_hours": labor_hrs,
            "created_at": now,
            "updated_at": now,
            "version": 1,
        })
    await db.construction_division26.insert_many(div_docs)
    print(f"Inserted {len(div_docs)} Division 26 catalog items.")

    # ───── Projects + estimates + logs + blueprints ─────
    for proj in SEED_PROJECTS:
        project_doc = {
            "job_number": proj["job_number"],
            "client_name": proj["client_name"],
            "site_address": proj["site_address"],
            "contract_value": float(proj["contract_value"]),
            "current_phase": proj["current_phase"],
            "owner_id": "seed-system",
            "owner_name": "Seed System",
            "created_at": now,
            "updated_at": now,
            "created_by": "seed-system",
            "updated_by": "seed-system",
            "version": 1,
        }
        proj_result = await db.construction_projects.insert_one(project_doc)
        project_id = str(proj_result.inserted_id)
        print(f"  Project: {proj['job_number']} → {project_id}")

        # Estimate version
        crew = proj["crew_blend"]
        blend_sum = crew["foreman_ratio"] + crew["journeyman_ratio"] + crew["apprentice_ratio"]
        if abs(blend_sum - 1.0) > 0.001:
            raise ValueError(f"Crew blend for {proj['job_number']} does not sum to 1.0: {blend_sum}")

        resolved_items = []
        total_direct = 0.0
        total_labor_hours = 0.0
        for item_id, qty, mults in proj["line_items"]:
            cat = await db.construction_division26.find_one({"item_id": item_id})
            if not cat:
                raise ValueError(f"Division 26 item not found: {item_id}")
            calc = _calc_extended(
                cat["default_material_cost"], cat["default_labor_hours"], qty,
                mults, crew["blended_hourly_rate"], crew["fringe_burden"],
            )
            total_labor_hours += cat["default_labor_hours"] * qty
            total_direct += calc["direct_cost"]
            resolved_items.append({
                "item_id": item_id,
                "csi_code": cat["csi_code"],
                "description": cat["description"],
                "uom": cat["uom"],
                "quantity": float(qty),
                "applied_multipliers": list(mults),
                "base_material_cost": cat["default_material_cost"],
                "base_labor_hours": cat["default_labor_hours"],
                **calc,
            })

        target_margin = 0.20
        sell_price = total_direct / (1.0 - target_margin) if target_margin < 1.0 else 0.0
        gross_margin = (sell_price - total_direct) / sell_price if sell_price else 0.0

        version_doc = {
            "project_id": project_id,
            "version_number": 1,
            "target_margin": target_margin,
            "notes": f"Seed baseline — {proj['client_name']}",
            "crew_blend": crew,
            "line_items": resolved_items,
            "total_direct_cost": round(total_direct, 2),
            "total_labor_hours": round(total_labor_hours, 2),
            "sell_price": round(sell_price, 2),
            "gross_margin": round(gross_margin, 4),
            "created_by": "seed-system",
            "created_at": now,
        }
        await db.construction_estimate_versions.insert_one(version_doc)

        # Bump project version
        await db.construction_projects.update_one(
            {"_id": proj_result.inserted_id},
            {"$set": {"version": 2, "updated_at": now, "updated_by": "seed-system"}},
        )

        # Daily logs — simulate field progress to populate benchmarks
        log_count = 0
        for item_id, qty, mults in proj["line_items"]:
            cat = await db.construction_division26.find_one({"item_id": item_id})
            # Log ~40-70% of estimated quantity across 2-3 log entries
            installed = round(qty * 0.55, 2)
            hours = round(installed * cat["default_labor_hours"] * 1.1, 2)
            log_doc = {
                "project_id": project_id,
                "item_id": item_id,
                "actual_quantity_installed": installed,
                "actual_hours_spent": hours,
                "logged_by": "seed-system",
                "recorded_date": now,
                "created_at": now,
            }
            await db.construction_daily_logs.insert_one(log_doc)
            log_count += 1
        print(f"    Inserted {log_count} daily crew logs.")

        # Blueprints
        for sheet_number, file_path, scale_factor, layer_metadata in proj["blueprints"]:
            bp_doc = {
                "project_id": project_id,
                "sheet_number": sheet_number,
                "file_path": file_path,
                "scale_factor": scale_factor,
                "layer_metadata": layer_metadata,
                "uploaded_by": "seed-system",
                "uploaded_at": now,
            }
            await db.construction_blueprints.insert_one(bp_doc)
        print(f"    Inserted {len(proj['blueprints'])} blueprints.")

    # ───── Recalculate benchmarks from logs (mirrors the DB trigger) ─────
    pipeline = [
        {"$group": {
            "_id": "$item_id",
            "avg_hours": {"$avg": "$actual_hours_spent"},
            "count": {"$sum": 1},
        }},
    ]
    agg = await db.construction_daily_logs.aggregate(pipeline).to_list(length=None)
    benchmark_docs = []
    for row in agg:
        item_id = row["_id"]
        avg = round(row["avg_hours"], 4)
        benchmark_docs.append({
            "item_id": item_id,
            "historical_avg_hours_per_unit": avg,
            "sample_count": row["count"],
            "last_updated": now,
        })
    if benchmark_docs:
        for bd in benchmark_docs:
            await db.construction_benchmarks.update_one(
                {"item_id": bd["item_id"]},
                {"$set": bd},
                upsert=True,
            )
    print(f"Recalculated {len(benchmark_docs)} labor benchmarks from field logs.")

    # Summary
    print("\n✅ Seed complete. Summary:")
    for proj in SEED_PROJECTS:
        print(f"  • {proj['job_number']} — {proj['client_name']} — ${proj['contract_value']:,} — {proj['current_phase']}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
