# 🖥️ Running W.A.I. / M.O.R.E. on Your Own Laptop — Step by Step

**What this is:** instructions to run your website's "brain" (the backend server, including
the AI) right on your laptop, so you can test everything before it goes live. Written
plain — no computer-science degree needed. Take it one step at a time.

**You will need:** this Windows laptop, an internet connection, and about 20 minutes.
**Good news:** your secret keys are already saved, so you can skip the hard part.

---

## ⭐ The 30-second version (for when you've done it once)
1. Double-click `start_backup_server.bat`
2. Wait until it says **Uvicorn running on http://0.0.0.0:8001**
3. Open a browser to **http://localhost:8001/api/health** → you should see `healthy`
4. Open **http://localhost:8001/api/puzzles/next** → you'll see a live puzzle. 🎉

The rest of this file explains every step slowly, plus how to test the AI and what to do if something breaks.

---

## STEP 1 — Open a "terminal" in the project folder
A *terminal* is just a box where you type commands.

1. Open **File Explorer** and go to the project folder:
   `C:\Users\lenovo\ancestral-sage-debug`
2. Click once in the **address bar** at the top (where the folder path is).
3. Type `cmd` and press **Enter**. A black window opens — that's your terminal. It's
   already "inside" the project folder. Leave it open.

---

## STEP 2 — Make sure Python is installed
Python is the language the server is written in.

1. In the black terminal window, type this and press Enter:
   ```
   py --version
   ```
2. **If you see something like `Python 3.11.x`** → great, skip to Step 3.
3. **If it says "not recognized"** → install Python:
   - Go to https://python.org/downloads
   - Download the latest **3.11+** installer and run it.
   - 🚨 IMPORTANT: on the first screen, **check the box that says "Add Python to PATH"**, then click Install.
   - Close and re-open the terminal (Step 1) and try `py --version` again.

---

## STEP 3 — Install the server's parts (one time only)
The server needs some helper packages (like ingredients in a recipe). On this laptop
they're already installed, but running this is safe and confirms it.

1. In the terminal, type:
   ```
   cd backend
   ```
2. Then:
   ```
   py -m pip install -r requirements.txt
   ```
3. Wait. If you see lots of **"Requirement already satisfied"** — perfect, everything's
   there. (First time on a brand-new laptop, this can take a few minutes.)

---

## STEP 4 — Your secret keys (already done ✅)
The server needs keys to reach the database and the AI. **Yours are already saved** in the
file `backend\.env`. You don't need to type them again.

- To peek at them: open `backend\.env` in **Notepad**.
- 🔒 **Never** share this file, never post it, never screen-share it — it has live keys.
- The only blank ones are optional **voice** settings (ElevenLabs). You can ignore those
  unless you want the AI to talk out loud.

---

## STEP 5 — Start the server
**Easiest way:** in File Explorer, double-click **`start_backup_server.bat`** in the
project folder. A window opens and starts the server.

**Or, from the terminal** (you're already in the `backend` folder from Step 3):
```
py -m uvicorn server:app --port 8001 --reload
```

✅ **You're running when you see a line like:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```
Leave this window open. (Closing it stops the server.)

---

## STEP 6 — Check the server is alive
Open your web browser and go to these addresses:

1. **http://localhost:8001/api/health** → you should see a small bit of text saying it's
   healthy/ok. ✅ That means the server is up.
2. **http://localhost:8001/api/docs** → a big interactive list of everything the server
   can do. Scroll and you should spot the **new** ones:
   `/sovereign/chat`, `/sovereign/memory`, `/puzzles/next`, `/puzzles/answer`,
   `/partnership/status`.

---

## STEP 7 — See a brand-new feature work (no login needed)
Go to: **http://localhost:8001/api/puzzles/next**

You'll see a real puzzle in plain text (JSON), like:
```
{"done": false, "level": 1, "puzzle": {"question": "I'm tall when I'm young..."}}
```
That's **The Sovereign's puzzle game**, live on your laptop. 🎉

---

## STEP 8 — Talk to the AI (The Sovereign) — needs your exec login
The Sovereign is executive-only, so you must be logged in as your admin account.
The simplest no-coding way uses the `/api/docs` page:

1. Open **http://localhost:8001/api/docs**
2. Find **POST `/auth/login`** → click it → click **"Try it out"** → type your executive
   email and password in the boxes → click **Execute**.
3. In the response, copy the long `access_token` value (the text between the quotes).
4. Scroll to the top of the page, click the green **"Authorize"** button, paste the token,
   and confirm.
5. Now find **POST `/sovereign/chat`** → "Try it out" → in the box type:
   ```
   {"message": "Find me two HBCU residency bookings for Black History Month."}
   ```
   → **Execute**. The Sovereign replies. 🎉 (This uses real AI and spends a little of your
   **Anthropic** credit — that's normal.)

---

## STEP 9 — Run the automatic self-tests (proof it all works)
These check the new code without spending any AI credit. In a terminal in the `backend`
folder, run each:
```
py verify_new_engines.py
```
Expect: **ALL ENGINE + STRESS TESTS PASSED**
```
py verify_endpoints.py
```
Expect: **ENDPOINT VERIFICATION: 14/14 checks -> ALL PASS**

---

## STEP 10 (OPTIONAL) — Run the actual website too
If you want to click around the real site (not just the server):

1. Open a **second** terminal (Step 1) and type:
   ```
   cd frontend
   npm install
   npm start
   ```
2. A browser opens at **http://localhost:3000**.
3. ⚠️ If the site can't reach the server, open `frontend\.env` in Notepad, change every
   **`8000`** to **`8001`** (so it matches the server's port), save, and restart `npm start`.

---

## 🛑 How to stop everything
- Click the server window and press **Ctrl + C**, or just **close the window(s)**.

---

## 🔧 If something breaks (common fixes)
- **"py is not recognized"** → Python isn't installed or PATH wasn't checked. Redo Step 2.
- **"ModuleNotFoundError: No module named 'routers'"** → you're on an old copy; the current
  code already guards this. Make sure you're running the latest `backend\server.py`.
- **"Address already in use" / port 8001 busy** → something's already running on 8001. Close
  old server windows, or start with a different port: `--port 8002` (then use that number
  in the browser).
- **AI error / 502 on `/sovereign/chat`** → check `ANTHROPIC_API_KEY` in `backend\.env` is
  correct, and that you have internet. Remember AI calls use your Anthropic credit.
- **Database errors** → check `MONGO_URL` in `backend\.env` and that you're online. Local
  testing uses the separate `DB_NAME=wai_localtest` database, so it won't touch production.
- **Login fails** → use your executive admin account. (Your `.env` has an exec auto-reset
  setting, so the exec account is kept active on startup.)

---

## 🔒 Safety reminders
- `backend\.env` holds your **real, live** keys (Anthropic, MongoDB, Stripe) and your exec
  password. It's already hidden from git (safe), but **never** share or screen-share it.
- "Local" is fully separate from your live Railway site — running this does **not** change
  your real website.
