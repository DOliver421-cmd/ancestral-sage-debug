"""
WAI-Institute — MongoDB backup to local hard drive.
Runs standalone; does NOT need the full backend environment.

Setup (one time):
  1. Create C:\\WAI_Backups\\config.env with your MongoDB credentials:
         MONGO_URL=mongodb+srv://...
         DB_NAME=your_db_name
  2. Register the scheduled task (run once as Administrator):
         python backup_wai.py --install
  3. To run a backup immediately:
         python backup_wai.py

Backups are saved to BACKUP_DIR as timestamped folders.
The last KEEP_BACKUPS snapshots are kept; older ones are deleted.
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
BACKUP_DIR   = Path(r"C:\WAI_Backups\snapshots")
CONFIG_FILE  = Path(r"C:\WAI_Backups\config.env")
LOG_FILE     = Path(r"C:\WAI_Backups\backup.log")
KEEP_BACKUPS = 14          # 7 days at 2x/day
SYNC_HOURS   = 12          # scheduled task interval

# Collections that hold real user data — backed up in full.
USER_COLLECTIONS = [
    "users",
    "progress",
    "lab_submissions",
    "compliance_progress",
    "user_credentials",
    "attendance",
    "incidents",
    "audit_log",
    "notifications",
    "more_posts",
    "more_needs",
    "chat_history",
    "ai_consents",
    "tool_checkouts",
    "inventory",
    "sites",
    "mode_decisions",
]

# Collections seeded from code on every startup — small, still worth backing up.
SEED_COLLECTIONS = ["modules", "labs"]

ALL_COLLECTIONS = USER_COLLECTIONS + SEED_COLLECTIONS

# ── Helpers ────────────────────────────────────────────────────────────────────
def log(msg: str):
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    """Read MONGO_URL and DB_NAME from config.env."""
    if not CONFIG_FILE.exists():
        log(f"ERROR: Config file not found: {CONFIG_FILE}")
        log("Create it with:")
        log("  MONGO_URL=mongodb+srv://...")
        log("  DB_NAME=your_database_name")
        sys.exit(1)
    cfg = {}
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    if "MONGO_URL" not in cfg or "DB_NAME" not in cfg:
        log("ERROR: config.env must contain MONGO_URL and DB_NAME")
        sys.exit(1)
    return cfg


def bson_default(obj):
    """JSON serializer for types Motor returns that json.dumps can't handle."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


# ── Core backup ───────────────────────────────────────────────────────────────
async def run_backup():
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except ImportError:
        log("ERROR: motor not installed. Run: pip install motor")
        sys.exit(1)

    cfg    = load_config()
    client = AsyncIOMotorClient(cfg["MONGO_URL"], serverSelectionTimeoutMS=15000)
    db     = client[cfg["DB_NAME"]]

    ts       = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snap_dir = BACKUP_DIR / ts
    snap_dir.mkdir(parents=True, exist_ok=True)
    log(f"Backup started → {snap_dir}")

    total_docs = 0
    manifest   = {"timestamp": ts, "collections": {}}

    for col_name in ALL_COLLECTIONS:
        try:
            col   = db[col_name]
            docs  = await col.find({}, {"_id": 0}).to_list(length=None)
            count = len(docs)
            out   = snap_dir / f"{col_name}.json"
            out.write_text(
                json.dumps(docs, indent=2, default=bson_default, ensure_ascii=False),
                encoding="utf-8",
            )
            manifest["collections"][col_name] = count
            total_docs += count
            log(f"  {col_name:30s} {count:>6} docs")
        except Exception as e:
            log(f"  {col_name:30s} ERROR: {e}")
            manifest["collections"][col_name] = f"ERROR: {e}"

    # Write manifest
    (snap_dir / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    client.close()
    log(f"Backup complete. {total_docs} total documents saved.")

    # Rotate: delete oldest if we have more than KEEP_BACKUPS
    snapshots = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.name)
    while len(snapshots) > KEEP_BACKUPS:
        old = snapshots.pop(0)
        shutil.rmtree(old, ignore_errors=True)
        log(f"Rotated old backup: {old.name}")

    log("-" * 60)


# ── Windows Task Scheduler install ────────────────────────────────────────────
def install_task():
    """Register a Windows scheduled task that runs this script every 12 hours."""
    script  = Path(__file__).resolve()
    python  = Path(sys.executable).resolve()
    trigger = f"PT{SYNC_HOURS}H"   # ISO 8601 duration

    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>{trigger}</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2026-01-01T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
    <BootTrigger><Enabled>true</Enabled></BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python}</Command>
      <Arguments>"{script}"</Arguments>
      <WorkingDirectory>{script.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = Path(r"C:\WAI_Backups\wai_backup_task.xml")
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml, encoding="utf-16")

    result = subprocess.run(
        ["schtasks", "/Create", "/TN", "WAI_Database_Backup",
         "/XML", str(xml_path), "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Scheduled task 'WAI_Database_Backup' created.")
        print(f"Runs every {SYNC_HOURS} hours and on boot.")
        print(f"Backups saved to: {BACKUP_DIR}")
        print(f"Log file: {LOG_FILE}")
    else:
        print("Failed to create scheduled task:")
        print(result.stderr or result.stdout)
        print("\nYou may need to run this script as Administrator.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WAI MongoDB backup tool")
    parser.add_argument(
        "--install", action="store_true",
        help="Register Windows scheduled task (run as Administrator)"
    )
    args = parser.parse_args()

    if args.install:
        install_task()
    else:
        asyncio.run(run_backup())
