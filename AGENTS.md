# WAI-Institute Project Brief

## Quick Start
- **Start server:** `cd backend && python -m server` (runs on port 8001)
- **Run simulation:** `cd backend && python -m tests.revenue_simulation`
- **Run tests:** `cd backend && python -m pytest tests/ -v`
- **Verify endpoints:** `cd backend && python scripts/tools/verify_endpoints.py`
- **Deploy simulation:** `cd backend && python scripts/tools/deploy_sim.py`

## Project Structure
```
ancestral-sage-debug/
├── app/                          # Main application
├── backend/                      # Python backend
│   ├── ai/persona_loader.py      # 17 personas (prompts + capabilities)
│   ├── server.py                 # Main API server (~9900 lines)
│   ├── wai_institute/
│   │   ├── core/                 # PRT, The 9, authority modules
│   │   └── personas/             # Persona-specific engines
│   ├── tests/
│   │   ├── revenue_simulation.py # 5-scenario simulation suite
│   │   └── test_critical_paths.py
│   └── scripts/tools/            # Diagnostics & utilities
├── frontend/                     # React frontend
├── scripts/                      # Ops & deploy scripts
└── opencode.json                 # opencode config (safe defaults)
```

## Key Commands (via opencode.json)
- `opencode simulate` — run revenue simulation
- `opencode test` — run critical path tests
- `opencode doctor` — run backend diagnostics
- `opencode verify` — run endpoint smoke tests
- `opencode seed` — start backend server
- `opencode status` — show git status + recent log

## Persona System (17 personas)
- **Tier 1:** NAM Oshun / Delon Oliver (human)
- **Tier 2:** Director
- **Tier 3:** Assistant Director
- **Tier 4:** Ancestral Sage, Revenue Director, Cipher, Oracle, Ambassador, Architect, Savant Scholar, Apprentice, Product Designer, Risk Officer, Strategic Navigator, WAI Success Engine, Confidentiality Sentinel, Poor Righteous Teacher
- **Tier 5:** Elder Council
- **Fusion:** The 9 (unified mind)

Each T4 persona has VERIFIED ACTIVE CAPABILITIES (tool access) and produces sellable digital products ($9.99-$349.00). Revenue projection: $16K-$71K/yr at slow-to-moderate demand.

## Safety Rules
- `rm`, `rm -rf`, `git reset --hard`, `git push --force` are DENIED
- `git push` requires confirmation
- Code edits are allowed; bash commands require approval
- Always ask before running server or making infrastructure changes
