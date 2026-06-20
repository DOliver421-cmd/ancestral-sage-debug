WAI-INSTITUTE.ORG — FULL CODEBASE EXPORT
=========================================

This bundle contains the complete codebase for the W.A.I. application,
exported from the Emergent preview environment.

WHAT'S INCLUDED
---------------
- backend/         FastAPI app, system prompts, tests, migrations, seed scripts
- frontend/        React app (src, public, package.json, tailwind, configs)
- memory/          PRD.md, CHANGELOG.md, test_credentials.md
- test_reports/    Past testing-subagent JSON reports
- tests/           Top-level test artifacts
- evidence_bundle/ Billing/compliance audit artifacts
- .git/            Full git history (4.4 MB)
- .emergent/       Platform metadata (safe to delete on migration)
- All root .md files: README, P0_PRODUCTION_AUDIT, EXECUTIVE_SUMMARY_*,
  PR_NOTES, RUNBOOK_P1, design_guidelines.json, EVIDENCE_BUNDLE.zip,
  test_result.md, yarn.lock, .gitignore, .gitconfig

WHAT'S EXCLUDED (and how to restore)
------------------------------------
- frontend/node_modules/  → run `cd frontend && yarn install`
- backend/__pycache__/    → auto-regenerated on first Python run
- .ruff_cache/            → auto-regenerated on first ruff run
- .pytest_cache/          → auto-regenerated on first pytest run

These are all auto-regenerated from package.json / requirements.txt and
should never be shipped. Excluding them dropped the bundle from 540 MB
to ~5 MB.

QUICK SETUP ON ANY SERVER
-------------------------
1. Extract:
     tar -xzf wai-codebase.tar.gz
     cd app

2. Backend (Python 3.11+, MongoDB running):
     cd backend
     python -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     cp .env.example .env   # or recreate the .env below
     uvicorn server:app --host 0.0.0.0 --port 8001 --reload

3. Frontend (Node 18+, yarn):
     cd ../frontend
     yarn install
     # set REACT_APP_BACKEND_URL in .env to your backend
     yarn start

4. Seed initial accounts:
     cd backend
     python seed_exec_admin.py

REQUIRED ENVIRONMENT VARIABLES
------------------------------
Backend (backend/.env):
  MONGO_URL=mongodb://localhost:27017
  DB_NAME=wai_institute
  JWT_SECRET=<a long random string>
  EMERGENT_LLM_KEY=<your LLM key, or replace with OPENAI_API_KEY usage>
  RESEND_API_KEY=<for password-reset emails>
  RESEND_FROM=<verified Resend sender>
  PUBLIC_APP_URL=https://your-domain.com

Frontend (frontend/.env):
  REACT_APP_BACKEND_URL=https://api.your-domain.com

EMERGENT-SPECIFIC DEPENDENCIES TO REMOVE FOR FULL PORTABILITY
-------------------------------------------------------------
The codebase imports `emergentintegrations` (lines visible via:
  grep -rn "emergentintegrations" backend/server.py
) — currently used for:
  - AI chat (Claude Sonnet via Emergent LLM key)
  - TTS (OpenAI TTS via Emergent LLM key)

To run fully off Emergent:
1. pip install openai anthropic
2. Replace `emergentintegrations.llm.chat.LlmChat` calls with native
   `anthropic.Anthropic()` client calls.
3. Replace `emergentintegrations.llm.openai.OpenAITextToSpeech` with
   native `openai.audio.speech.create(model="tts-1", voice="sage", ...)`.
4. Set OPENAI_API_KEY and ANTHROPIC_API_KEY env vars.

Total swap: ~30 lines of code.

ADMIN ACCOUNTS (from memory/test_credentials.md)
------------------------------------------------
Executive Admin: delon.oliver@lightningcityelectric.com / Executive@LCE2026
Admin:           admin@lcewai.org                       / Admin@LCE2026
Instructor:      instructor@lcewai.org                  / Teach@LCE2026
Student:         student@lcewai.org                     / Learn@LCE2026

CHANGE ALL OF THESE IMMEDIATELY on a fresh install — these are
documented for testing/handoff only.

TESTS
-----
cd backend
pytest tests/ -v       # 262 tests at last count

FILES YOU MAY WANT TO REVIEW FIRST
----------------------------------
- memory/PRD.md          Product requirements + history
- memory/CHANGELOG.md    Every change shipped, dated
- backend/server.py      Main FastAPI app (~3500 lines)
- backend/prompts/ancestral_sage_prompt.py  Authoritative Sage persona
- frontend/src/App.js    React router root
- frontend/src/pages/    All page components

GOOD LUCK
---------
The codebase is portable. MongoDB, React, FastAPI — all open standards.
Nothing in here locks you to Emergent except the two emergentintegrations
imports noted above. Strip those and the app runs anywhere with Python +
Node + Mongo.
