# WAI Institute Scripts

## Directory Layout

```
scripts/
├── ops/          # Operational tools (gitignored — may contain local paths)
│   ├── clear_lockouts.py      # Clear exec account lockouts
│   ├── reset_password.py      # Emergency password reset
│   ├── start_backup_server.bat  # Home backup server launcher (Windows)
│   ├── start_backup_server.sh   # Home backup server launcher (Linux/Mac)
│   └── backup_wai.py           # Database backup utility
├── tools/        # Development & test utilities (tracked)
│   ├── deploy_sim.py           # Railway deployment simulation
│   ├── verify_endpoints.py     # Endpoint smoke tests
│   ├── verify_new_engines.py   # Engine validation
│   ├── find_user.py            # User lookup tool
│   └── ...
└── README.md
```

## Redundancy Tiers

| Tier | Host | Access |
|------|------|--------|
| **Primary** | Railway (production) | `https://ancestral-sage-debug-production.up.railway.app` |
| **Backup** | Home server + Cloudflare Tunnel | See `start_backup_server.bat` |
| **Emergency** | Standalone HTML UI | `/emergency` on any running backend |
| **Database** | MongoDB Atlas (primary) | MONGO_URL env var |
| **Database Backup** | MongoDB Atlas (backup) | MONGO_BACKUP_URL env var |

## Emergency Recovery

If locked out of exec accounts:
1. Set `EXEC_FORCE_RESET=1` in Railway env vars + redeploy
2. Or use `scripts/ops/clear_lockouts.py` against the DB directly
3. Or use the standalone copy at `.archive/emergency/clear_lockouts.py`
