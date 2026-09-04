# Owner Account & BYOK Recovery Runbook

## When to use this
You (owner, `youpickeddoliver@gmail.com` / `NAM Oshun` / `souppoetry@gmail.com`, exec seats
in `backend/reset_exec_accounts.py` and `backend/server.py` Mode A) are locked out of your
exec account, your BYOK keys stopped working after a restart, or the free-tier API gateway
denies you access that should be free.

## This is an ENVIRONMENT recovery, not a code defect
Verified: `backend/byok.py`, `backend/ai/llm_gateway.py`, `backend/security/feature_control.py`,
and the deploy configs (`Dockerfile`, `docker-compose.yml`, `daytona.yaml`, `railway.toml`)
are correct. BYOK routes your own key first and is **free for `executive_admin`**
(see `backend/roles.py` `FREE_BYOK_ROLES`). Feature flags safe-default to *allow*
(`feature_control.py`: absent config == allow; only an explicit `enabled:false` blocks).

The lockout comes from missing/lost live environment, not from repo code:
- `MONGO_URL` unset -> DB disabled -> account + BYOK-key reads fail -> locked out.
- `PROVIDER_KEY_ENCRYPTION_SECRET` unset -> `keyvault.py` falls back to an **ephemeral**
  per-process key -> BYOK keys encrypted in one process cannot decrypt after a restart.

## Step 1 — Reclaim your exec seat (owner only)
### Option A — Boot-time force reset (Railway env; no direct DB access required)
Set on Railway Variables, redeploy, then **log in**, then **delete these vars immediately**
(`server.py` Mode A/B resets the password on every boot while the flag stays set):
```
EXEC_FORCE_RESET=1
EXEC_FORCE_RESET_EMAIL=youpickeddoliver@gmail.com     # your exec seat
EXEC_FORCE_RESET_PASSWORD=<strong password you choose>
```
Also ensure these exist so the app can find/grant your seat:
```
EXEC_ADMIN_EMAIL=youpickeddoliver@gmail.com
NAM_EXEC_EMAIL=souppoetry@gmail.com
MONGO_URL=<your live MongoDB URI>                     # e.g. mongodb+srv://... or your Atlas URI
DB_NAME=ancestral_sage
```

### Option B — Direct Mongo reset (if you can reach the DB yourself)
```bash
MONGO_URL=<your live MongoDB URI> DB_NAME=ancestral_sage \
EXEC_PASSWORD_1=<your pw> EXEC_PASSWORD_2=<nam pw> \
  python reset_exec_accounts.py
```
Seats: Delon Oliver `youpickeddoliver@gmail.com`, NAM Oshun `souppoetry@gmail.com`.
The script sets `role=executive_admin`, `is_active=True`, and clears `login_locked_until`.

## Step 2 — Restore the data + key-encryption layer
```
MONGO_URL=<your live MongoDB URI>
DB_NAME=ancestral_sage
PROVIDER_KEY_ENCRYPTION_SECRET=<stable Fernet key>    # generate ONCE:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
`backend/keyvault.py` resolves the secret: env var -> persisted in `db.platform_config["fernet_secret"]`
(auto-saved on first boot with a DB) -> ephemeral. **If Mongo was down when you originally
saved your BYOK key, it was encrypted ephemeral and cannot be decrypted** (go to Step 3).
With Mongo reachable + this secret stable, existing BYOK keys decrypt automatically.

## Step 3 — Re-attach your BYOK key (only if keys won't decrypt)
`POST /api/byok/activate`, then save your Groq / Cerebras / Gemini key via the BYOK UI.
BYOK is **$0 for `executive_admin`** (`roles.py` `FREE_BYOK_ROLES`). You keep your
provider-account keys; no key values are stored in this repo.

## Step 4 — Confirm no live flag blocks AI/BYOK
`db.platform_flags` safe-defaults to allow. If an executive (or a prior session) wrote
`enabled:false` for `ai_chat` or `byok`, flip it back to `enabled:true` via the exec panel
(`/admin/control` -> Platform flags) or:
```js
db.platform_flags.update({"flags.ai_chat.enabled": false},
                         {$set: {"flags.ai_chat.enabled": true}})
```

## Important
- **Delete `EXEC_FORCE_RESET` after logging in**, or the password resets on every redeploy.
- Never commit `.env` / provider keys to the repo (`.gitignore` already blocks `.env*`).
