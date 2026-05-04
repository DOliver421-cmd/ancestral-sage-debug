"""LCE-WAI training platform backend.

FastAPI + MongoDB + JWT auth + Claude Sonnet 4.5 AI tutor + PDF certificates.
"""
import io
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Literal

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from starlette.middleware.cors import CORSMiddleware

from seed import MODULES, quiz_for
from seed_labs import ONLINE_LABS, IN_PERSON_LABS, COMPETENCIES
from seed_credentials import CREDENTIALS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGO = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_HOURS = int(os.environ.get('JWT_EXPIRE_HOURS', '168'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI(title="LCE-WAI Training Platform")
api_router = APIRouter(prefix="/api")
logger = logging.getLogger("lcewai")
logging.basicConfig(level=logging.INFO)

Role = Literal["student", "instructor", "admin"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegisterReq(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Role = "student"
    associate: Optional[str] = None


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class QuizQ(BaseModel):
    q: str
    options: List[str]
    answer: int


class Module(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    order: int
    slug: str
    title: str
    summary: str
    objectives: List[str]
    safety: List[str]
    tools: List[str]
    scripture: dict
    tasks: List[str]
    competencies: List[str]
    hours: int
    quiz: List[QuizQ] = []


class ProgressEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    module_slug: str
    status: Literal["not_started", "in_progress", "completed"] = "in_progress"
    quiz_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    hours_logged: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuizSubmit(BaseModel):
    module_slug: str
    answers: List[int]


class AIChatReq(BaseModel):
    session_id: str
    message: str
    module_slug: Optional[str] = None
    mode: Literal["tutor", "scripture", "quiz_gen", "explain"] = "tutor"


def hash_pw(p: str) -> str:
    return pwd_ctx.hash(p)


def verify_pw(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)


def make_token(user_id: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)


async def current_user(authorization: Optional[str] = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")
    return User(**user_doc)


def require_role(*roles):
    async def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"Requires role: {roles}")
        return user
    return dep


async def seed_modules():
    for m in MODULES:
        existing = await db.modules.find_one({"slug": m["slug"]})
        doc = {**m, "quiz": quiz_for(m["slug"])}
        if existing:
            await db.modules.update_one({"slug": m["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.modules.insert_one(doc)
    logger.info("Seeded %d modules", len(MODULES))


async def seed_users():
    seeds = [
        ("admin@lcewai.org", "LCE-WAI Admin", "admin", None, "Admin@LCE2026"),
        ("instructor@lcewai.org", "Jordan Rivera", "instructor", "Associate-Alpha", "Teach@LCE2026"),
        ("student@lcewai.org", "Alex Carter", "student", "Associate-Alpha", "Learn@LCE2026"),
    ]
    for email, name, role, associate, pw in seeds:
        if not await db.users.find_one({"email": email}):
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": email,
                "full_name": name,
                "role": role,
                "associate": associate,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "password_hash": hash_pw(pw),
            })


async def seed_labs():
    for spec in ONLINE_LABS:
        doc = {**spec, "track": "online"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)
    for spec in IN_PERSON_LABS:
        doc = {**spec, "track": "inperson"}
        existing = await db.labs.find_one({"slug": doc["slug"]})
        if existing:
            await db.labs.update_one({"slug": doc["slug"]}, {"$set": doc})
        else:
            doc["id"] = str(uuid.uuid4())
            await db.labs.insert_one(doc)


@app.on_event("startup")
async def on_startup():
    await seed_modules()
    await seed_users()
    await seed_labs()


@api_router.get("/")
async def root():
    return {"app": "LCE-WAI Training Platform", "status": "ok"}


@api_router.post("/auth/register", response_model=TokenResp)
async def register(body: RegisterReq):
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")
    user = User(email=body.email, full_name=body.full_name, role=body.role, associate=body.associate)
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["password_hash"] = hash_pw(body.password)
    await db.users.insert_one(doc)
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginReq):
    doc = await db.users.find_one({"email": body.email}, {"_id": 0})
    if not doc or not verify_pw(body.password, doc["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"])
    doc.pop("password_hash", None)
    user = User(**doc)
    return TokenResp(access_token=make_token(user.id, user.role), user=user)


@api_router.get("/auth/me", response_model=User)
async def me(user: User = Depends(current_user)):
    return user


@api_router.get("/modules", response_model=List[Module])
async def list_modules(user: User = Depends(current_user)):
    docs = await db.modules.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return [Module(**d) for d in docs]


@api_router.get("/modules/{slug}", response_model=Module)
async def get_module(slug: str, user: User = Depends(current_user)):
    doc = await db.modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Module not found")
    return Module(**doc)


@api_router.get("/progress/me")
async def my_progress(user: User = Depends(current_user)):
    docs = await db.progress.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@api_router.post("/progress/start")
async def start_module(payload: dict, user: User = Depends(current_user)):
    slug = payload.get("module_slug")
    if not slug:
        raise HTTPException(400, "module_slug required")
    existing = await db.progress.find_one({"user_id": user.id, "module_slug": slug}, {"_id": 0})
    if existing:
        return existing
    entry = ProgressEntry(user_id=user.id, module_slug=slug, status="in_progress")
    doc = entry.model_dump()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.progress.insert_one(doc)
    return doc


@api_router.post("/progress/quiz")
async def submit_quiz(body: QuizSubmit, user: User = Depends(current_user)):
    mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    quiz = mod.get("quiz", [])
    if len(body.answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == body.answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    status_val = "completed" if score >= 70 else "in_progress"
    completed_at = datetime.now(timezone.utc).isoformat() if status_val == "completed" else None
    update = {
        "user_id": user.id,
        "module_slug": body.module_slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": completed_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.progress.update_one(
        {"user_id": user.id, "module_slug": body.module_slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await award_credentials(user.id)
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val}


@api_router.get("/roster")
async def roster(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    result = []
    for s in students:
        prog = await db.progress.find({"user_id": s["id"]}, {"_id": 0}).to_list(100)
        completed = sum(1 for p in prog if p.get("status") == "completed")
        hours = sum(p.get("hours_logged", 0) for p in prog if p.get("status") == "completed")
        scored = [p.get("quiz_score") for p in prog if p.get("quiz_score") is not None]
        avg_score = sum(scored) / len(scored) if scored else 0
        result.append({**s, "modules_completed": completed, "hours": hours, "avg_score": round(avg_score, 1)})
    return result


@api_router.get("/admin/users")
async def all_users(user: User = Depends(require_role("admin"))):
    return await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(5000)


@api_router.post("/admin/associate")
async def assign_associate(payload: dict, user: User = Depends(require_role("admin"))):
    uid = payload.get("user_id")
    associate = payload.get("associate")
    if not uid:
        raise HTTPException(400, "user_id required")
    await db.users.update_one({"id": uid}, {"$set": {"associate": associate}})
    return {"ok": True}


@api_router.get("/admin/stats")
async def stats(user: User = Depends(require_role("admin"))):
    return {
        "users": await db.users.count_documents({}),
        "students": await db.users.count_documents({"role": "student"}),
        "instructors": await db.users.count_documents({"role": "instructor"}),
        "modules": await db.modules.count_documents({}),
        "completions": await db.progress.count_documents({"status": "completed"}),
    }


SYSTEM_PROMPTS = {
    "tutor": "You are a patient master electrician and faith-forward mentor for the Lightning City Electric Workforce & Apprenticeship Institute (LCE-WAI). Answer apprentice questions clearly, reference NEC articles when relevant, emphasize safety, and use plain language. Keep replies under 250 words.",
    "scripture": "You are a faith-based electrical trade mentor at LCE-WAI. For each question, give a short encouragement tying the apprentice's current work to a relevant scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified.",
    "quiz_gen": "You generate short multiple-choice quiz questions (4 options, mark the correct answer index 0-3) on electrical topics. Output a clean numbered list with answer key at the end.",
    "explain": "You explain electrical concepts step-by-step to apprentices. Use analogies, list steps, and close with a 1-line 'Safety first' reminder.",
}


@api_router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")

    ctx = ""
    if body.module_slug:
        mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
        if mod:
            ctx = f"\n\nCurrent module: {mod['title']}. Objectives: {'; '.join(mod['objectives'])}. Safety: {'; '.join(mod['safety'])}."

    system = SYSTEM_PROMPTS.get(body.mode, SYSTEM_PROMPTS["tutor"]) + ctx
    session_id = f"{user.id}:{body.session_id}"
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=system).with_model(
        "anthropic", "claude-sonnet-4-5-20250929"
    )
    try:
        reply = await chat.send_message(UserMessage(text=body.message))
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "session_id": body.session_id,
        "mode": body.mode,
        "module_slug": body.module_slug,
        "user_msg": body.message,
        "assistant_msg": reply,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply}


@api_router.get("/ai/history/{session_id}")
async def ai_history(session_id: str, user: User = Depends(current_user)):
    return await db.chat_history.find(
        {"user_id": user.id, "session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)


@api_router.get("/certificates/me")
async def my_certificates(user: User = Depends(current_user)):
    prog = await db.progress.find(
        {"user_id": user.id, "status": "completed"}, {"_id": 0}
    ).to_list(200)
    certs = []
    for p in prog:
        mod = await db.modules.find_one({"slug": p["module_slug"]}, {"_id": 0})
        if mod:
            certs.append({
                "module_slug": p["module_slug"],
                "title": mod["title"],
                "hours": mod["hours"],
                "score": p.get("quiz_score"),
                "completed_at": p.get("completed_at"),
            })
    if len(certs) == len(MODULES):
        certs.append({
            "module_slug": "program",
            "title": "LCE-WAI Camper-to-Classroom Program Completion",
            "hours": sum(m["hours"] for m in MODULES),
            "score": sum((c["score"] or 0) for c in certs) / len(MODULES),
            "completed_at": max((c.get("completed_at") or "") for c in certs),
        })
    return certs


@api_router.get("/certificates/{slug}.pdf")
async def cert_pdf(slug: str, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    if slug == "program":
        title = "Camper-to-Classroom Program Completion"
        hours = sum(m["hours"] for m in MODULES)
    else:
        mod = await db.modules.find_one({"slug": slug}, {"_id": 0})
        if not mod:
            raise HTTPException(404, "Module not found")
        prog = await db.progress.find_one(
            {"user_id": user_doc["id"], "module_slug": slug, "status": "completed"}, {"_id": 0}
        )
        if not prog:
            raise HTTPException(404, "Not completed yet")
        title = mod["title"]
        hours = mod["hours"]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    w, h = landscape(letter)

    c.setFillColor(colors.HexColor("#F7F7F5"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(8)
    c.rect(0.35 * inch, 0.35 * inch, w - 0.7 * inch, h - 0.7 * inch, fill=0, stroke=1)
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.rect(0.35 * inch, h - 1.1 * inch, w - 0.7 * inch, 0.12 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 1.6 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 1.85 * inch, "LCE-WAI Partner Program")
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, h - 2.7 * inch, "Certificate of Completion")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 3.2 * inch, "This certifies that")
    c.setFillColor(colors.HexColor("#1E5BA8"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w / 2, h - 3.8 * inch, user_doc["full_name"])
    c.setFillColor(colors.HexColor("#0B203F"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 4.3 * inch, "has successfully completed")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w / 2, h - 4.85 * inch, title)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 5.3 * inch, f"Training Hours: {hours}    |    Date: {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.setStrokeColor(colors.HexColor("#0B203F"))
    c.setLineWidth(1)
    c.line(1.5 * inch, 1.1 * inch, 4 * inch, 1.1 * inch)
    c.line(w - 4 * inch, 1.1 * inch, w - 1.5 * inch, 1.1 * inch)
    c.setFont("Helvetica", 10)
    c.drawCentredString(2.75 * inch, 0.9 * inch, "Instructor of Record")
    c.drawCentredString(w - 2.75 * inch, 0.9 * inch, "Program Director")
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(w / 2, 0.55 * inch, '"Whatever you do, work at it with all your heart, as working for the Lord." - Colossians 3:23')
    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=LCE-WAI-{slug}.pdf"},
    )


# -- LAB MODELS --
class LabSubmitReq(BaseModel):
    lab_slug: Optional[str] = None
    answers: Optional[dict] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class LabReviewReq(BaseModel):
    status: Literal["approved", "rejected"]
    feedback: Optional[str] = None


def grade_online_lab(simulator_type: str, answers: dict) -> dict:
    """Return {'score': 0-100, 'correct': int, 'total': int, 'detail': str} for online labs."""
    if not answers:
        return {"score": 0, "correct": 0, "total": 1, "detail": "No answers submitted"}

    if simulator_type == "basic_circuit":
        v = float(answers.get("voltage", 0))
        r1, r2, r3 = float(answers.get("r1", 0)), float(answers.get("r2", 0)), float(answers.get("r3", 0))
        cfg = answers.get("config", "series")
        user_rt = float(answers.get("total_r", 0))
        user_i = float(answers.get("total_i", 0))
        if cfg == "series":
            rt = r1 + r2 + r3
        else:
            rt = 1 / ((1 / r1 if r1 else 0) + (1 / r2 if r2 else 0) + (1 / r3 if r3 else 0)) if (r1 and r2 and r3) else 0
        it = v / rt if rt else 0
        rt_ok = abs(user_rt - rt) < max(0.1, rt * 0.02)
        it_ok = abs(user_i - it) < max(0.01, it * 0.02)
        correct = int(rt_ok) + int(it_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Rt={rt:.2f}Ω, I={it:.3f}A (yours: Rt={user_rt}, I={user_i})"}

    if simulator_type == "switch_wiring":
        # expects answers: {hot_to: "brass", neutral_to: "silver", ground_to: "green"}
        key = {"hot_to": "brass", "neutral_to": "silver", "ground_to": "green"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / 3 * 100, "correct": correct, "total": 3, "detail": ""}

    if simulator_type == "panel_labeling":
        # answers: {slot_0: "kitchen", slot_1: "bedroom", ...}
        key = {"slot_0": "kitchen", "slot_1": "bedroom", "slot_2": "bathroom_gfci",
               "slot_3": "living_room", "slot_4": "hvac", "slot_5": "laundry"}
        correct = sum(1 for k, v in key.items() if answers.get(k) == v)
        return {"score": correct / len(key) * 100, "correct": correct, "total": len(key), "detail": ""}

    if simulator_type == "conduit_calc":
        rise = float(answers.get("rise", 0))
        angle = int(answers.get("angle", 30))
        user_distance = float(answers.get("distance", 0))
        user_shrink = float(answers.get("shrink", 0))
        mult_tbl = {10: (6.0, 1 / 16), 22: (2.6, 3 / 16), 30: (2.0, 1 / 4), 45: (1.4, 3 / 8), 60: (1.2, 1 / 2)}
        mult, shrink_per_inch = mult_tbl.get(angle, (2.0, 0.25))
        distance = rise * mult
        shrink = rise * shrink_per_inch
        d_ok = abs(user_distance - distance) < 0.25
        s_ok = abs(user_shrink - shrink) < 0.1
        correct = int(d_ok) + int(s_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"distance={distance:.2f}\" shrink={shrink:.3f}\""}

    if simulator_type == "vdrop":
        length = float(answers.get("length_ft", 0))
        current = float(answers.get("current_a", 0))
        awg = int(answers.get("awg", 12))
        source_v = float(answers.get("source_v", 120))
        user_vd_pct = float(answers.get("vd_pct", 0))
        cm_tbl = {14: 4110, 12: 6530, 10: 10380, 8: 16510, 6: 26240, 4: 41740, 2: 66360}
        cm = cm_tbl.get(awg, 6530)
        k = 12.9
        vd = (2 * k * current * length) / cm
        vd_pct = vd / source_v * 100
        ok = abs(user_vd_pct - vd_pct) < 0.2
        return {"score": 100 if ok else 0, "correct": int(ok), "total": 1,
                "detail": f"Actual Vdrop = {vd:.2f}V ({vd_pct:.2f}%)"}

    if simulator_type == "solar_config":
        daily_kwh = float(answers.get("daily_kwh", 0))
        sun_hours = float(answers.get("sun_hours", 0))
        sys_v = float(answers.get("sys_v", 48))
        autonomy_days = float(answers.get("autonomy_days", 2))
        user_pv_w = float(answers.get("pv_watts", 0))
        user_bank_ah = float(answers.get("bank_ah", 0))
        pv_w = (daily_kwh * 1000) / sun_hours if sun_hours else 0
        bank_wh = daily_kwh * 1000 * autonomy_days / 0.8
        bank_ah = bank_wh / sys_v if sys_v else 0
        pv_ok = abs(user_pv_w - pv_w) / max(1, pv_w) < 0.1
        ah_ok = abs(user_bank_ah - bank_ah) / max(1, bank_ah) < 0.1
        correct = int(pv_ok) + int(ah_ok)
        return {"score": correct / 2 * 100, "correct": correct, "total": 2,
                "detail": f"Need ~{pv_w:.0f}W array and ~{bank_ah:.0f}Ah bank"}

    if simulator_type == "loto":
        expected = ["notify", "shutdown", "lockout", "tagout", "verify_dead", "try_start"]
        seq = answers.get("sequence", [])
        correct = sum(1 for i, s in enumerate(expected) if i < len(seq) and seq[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "troubleshooting":
        # expected path: test_breaker, test_receptacle_voltage, test_neutral_continuity, find_open_neutral
        path = answers.get("path", [])
        expected = ["test_breaker", "test_receptacle_voltage", "test_neutral_continuity", "find_open_neutral"]
        correct = sum(1 for i, s in enumerate(expected) if i < len(path) and path[i] == s)
        return {"score": correct / len(expected) * 100, "correct": correct, "total": len(expected), "detail": ""}

    if simulator_type == "load_balance":
        assignments = answers.get("assignments", {})
        loads = {"c1": 1500, "c2": 800, "c3": 1200, "c4": 600, "c5": 1800, "c6": 400}
        a = sum(loads[k] for k, v in assignments.items() if v == "A" and k in loads)
        b = sum(loads[k] for k, v in assignments.items() if v == "B" and k in loads)
        diff_pct = abs(a - b) / max(1, (a + b) / 2) * 100 if (a + b) else 100
        ok = diff_pct <= 10
        return {"score": 100 if ok else max(0, 100 - diff_pct * 2), "correct": 1 if ok else 0, "total": 1,
                "detail": f"Phase A={a}W Phase B={b}W Δ={diff_pct:.1f}%"}

    return {"score": 0, "correct": 0, "total": 1, "detail": "Unknown simulator"}


# -- LAB ROUTES --
@api_router.get("/competencies")
async def list_competencies(user: User = Depends(current_user)):
    subs = await db.lab_submissions.find(
        {"user_id": user.id, "status": {"$in": ["approved", "passed"]}}, {"_id": 0}
    ).to_list(500)
    score_by_comp = {c["key"]: {"points": 0, "labs": 0} for c in COMPETENCIES}
    for s in subs:
        lab = await db.labs.find_one({"slug": s["lab_slug"]}, {"_id": 0})
        if not lab:
            continue
        for cmp_key in lab.get("competencies", []):
            if cmp_key in score_by_comp:
                score_by_comp[cmp_key]["points"] += lab.get("skill_points", 0)
                score_by_comp[cmp_key]["labs"] += 1
    return {
        "competencies": COMPETENCIES,
        "progress": score_by_comp,
        "total_points": sum(v["points"] for v in score_by_comp.values()),
        "total_labs": len(subs),
    }


@api_router.get("/labs")
async def list_labs(track: Optional[str] = None, user: User = Depends(current_user)):
    q = {"track": track} if track in ("online", "inperson") else {}
    docs = await db.labs.find(q, {"_id": 0}).to_list(200)
    my_subs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    sub_map = {s["lab_slug"]: s for s in my_subs}
    for d in docs:
        s = sub_map.get(d["slug"])
        d["my_submission"] = {
            "status": s["status"] if s else "not_started",
            "auto_score": s.get("auto_score") if s else None,
        } if s else {"status": "not_started"}
    docs.sort(key=lambda x: (x.get("track") == "inperson", x.get("slug", "")))
    return docs


@api_router.get("/labs/{slug}")
async def get_lab(slug: str, user: User = Depends(current_user)):
    doc = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Lab not found")
    sub = await db.lab_submissions.find_one({"user_id": user.id, "lab_slug": slug}, {"_id": 0})
    doc["my_submission"] = sub
    return doc


@api_router.post("/labs/{slug}/submit")
async def submit_lab(slug: str, body: LabSubmitReq, user: User = Depends(current_user)):
    lab = await db.labs.find_one({"slug": slug}, {"_id": 0})
    if not lab:
        raise HTTPException(404, "Lab not found")

    now = datetime.now(timezone.utc).isoformat()
    if lab["track"] == "online":
        result = grade_online_lab(lab.get("simulator_type", ""), body.answers or {})
        status_val = "passed" if result["score"] >= 70 else "failed"
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "online",
            "answers": body.answers or {},
            "auto_score": result["score"],
            "detail": result["detail"],
            "status": status_val,
            "feedback": None,
            "created_at": now,
            "reviewed_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        if status_val == "passed":
            await award_credentials(user.id)
        return {**result, "status": status_val}
    else:
        doc = {
            "user_id": user.id,
            "lab_slug": slug,
            "track": "inperson",
            "photo_url": body.photo_url,
            "notes": body.notes,
            "auto_score": None,
            "status": "pending",
            "feedback": None,
            "created_at": now,
        }
        await db.lab_submissions.update_one(
            {"user_id": user.id, "lab_slug": slug},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4())}},
            upsert=True,
        )
        return {"status": "pending"}


@api_router.get("/labs/submissions/me")
async def my_lab_submissions(user: User = Depends(current_user)):
    docs = await db.lab_submissions.find({"user_id": user.id}, {"_id": 0}).to_list(500)
    return docs


@api_router.get("/instructor/submissions")
async def pending_submissions(user: User = Depends(require_role("instructor", "admin"))):
    q = {"track": "inperson", "status": "pending"}
    docs = await db.lab_submissions.find(q, {"_id": 0}).to_list(500)
    for d in docs:
        u = await db.users.find_one({"id": d["user_id"]}, {"_id": 0, "password_hash": 0})
        lab = await db.labs.find_one({"slug": d["lab_slug"]}, {"_id": 0})
        d["user"] = u
        d["lab"] = lab
    return docs


@api_router.post("/instructor/submissions/{sub_id}/review")
async def review_submission(sub_id: str, body: LabReviewReq, user: User = Depends(require_role("instructor", "admin"))):
    sub = await db.lab_submissions.find_one({"id": sub_id}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.lab_submissions.update_one(
        {"id": sub_id},
        {"$set": {
            "status": body.status,
            "feedback": body.feedback,
            "reviewed_by": user.id,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if body.status == "approved":
        await award_credentials(sub["user_id"])
    return {"ok": True}


@api_router.get("/instructor/lab-report")
async def lab_report(user: User = Depends(require_role("instructor", "admin"))):
    q = {"role": "student"} if user.role == "admin" else {"role": "student", "associate": user.associate}
    students = await db.users.find(q, {"_id": 0, "password_hash": 0}).to_list(1000)
    result = []
    for s in students:
        subs = await db.lab_submissions.find({"user_id": s["id"]}, {"_id": 0}).to_list(500)
        passed = [x for x in subs if x.get("status") in ("passed", "approved")]
        pending = [x for x in subs if x.get("status") == "pending"]
        points = 0
        hours = 0
        for p in passed:
            lab = await db.labs.find_one({"slug": p["lab_slug"]}, {"_id": 0})
            if lab:
                points += lab.get("skill_points", 0)
                hours += lab.get("hours", 0)
        result.append({
            "user_id": s["id"],
            "full_name": s["full_name"],
            "email": s["email"],
            "associate": s.get("associate"),
            "labs_passed": len(passed),
            "labs_pending": len(pending),
            "skill_points": points,
            "lab_hours": hours,
        })
    return result


# -- CREDENTIALING & PORTFOLIO --
class PortfolioPublishReq(BaseModel):
    bio: Optional[str] = None
    publish: bool = True


async def get_user_state(user_id: str) -> dict:
    """Load modules, labs, competencies relevant for credential eligibility."""
    mod_progress = await db.progress.find(
        {"user_id": user_id, "status": "completed"}, {"_id": 0}
    ).to_list(500)
    completed_modules = {p["module_slug"] for p in mod_progress}
    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    passed_labs = {s["lab_slug"] for s in lab_subs}
    # competency points
    comp = {c["key"]: 0 for c in COMPETENCIES}
    for s in lab_subs:
        lab = await db.labs.find_one({"slug": s["lab_slug"]}, {"_id": 0})
        if lab:
            for k in lab.get("competencies", []):
                if k in comp:
                    comp[k] += lab.get("skill_points", 0)
    return {
        "completed_modules": completed_modules,
        "passed_labs": passed_labs,
        "competencies": comp,
        "module_count": len(completed_modules),
        "lab_count": len(passed_labs),
    }


def credential_eligible(cred: dict, state: dict) -> bool:
    trig = cred["trigger"]
    t = trig["type"]
    if t == "all_modules":
        return state["module_count"] >= len(MODULES)
    if t == "modules_all_of":
        return all(s in state["completed_modules"] for s in trig["slugs"])
    if t == "module_completed":
        return trig["slug"] in state["completed_modules"]
    if t == "labs_all_of":
        return all(s in state["passed_labs"] for s in trig["slugs"])
    if t == "lab_passed":
        return trig["slug"] in state["passed_labs"]
    if t == "competency_at_least":
        return state["competencies"].get(trig["key"], 0) >= trig["points"]
    return False


async def award_credentials(user_id: str) -> list:
    """Run all credential triggers and insert newly-earned credentials. Returns newly-awarded keys."""
    state = await get_user_state(user_id)
    awarded = []
    now = datetime.now(timezone.utc)
    for cred in CREDENTIALS:
        if not credential_eligible(cred, state):
            continue
        existing = await db.user_credentials.find_one(
            {"user_id": user_id, "credential_key": cred["key"]}, {"_id": 0}
        )
        if existing:
            # if expired, re-award (renewal); skip for MVP
            continue
        exp_months = cred.get("expires_months")
        expires_at = (now + timedelta(days=30 * exp_months)).isoformat() if exp_months else None
        await db.user_credentials.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "credential_key": cred["key"],
            "earned_at": now.isoformat(),
            "expires_at": expires_at,
            "status": "active",
        })
        awarded.append(cred["key"])
    return awarded


@api_router.get("/credentials")
async def list_credentials(user: User = Depends(current_user)):
    return CREDENTIALS


@api_router.get("/credentials/me")
async def my_credentials(user: User = Depends(current_user)):
    # re-run awards so fresh on page load
    await award_credentials(user.id)
    earned = await db.user_credentials.find({"user_id": user.id}, {"_id": 0}).to_list(200)
    cred_map = {c["key"]: c for c in CREDENTIALS}
    result = []
    now = datetime.now(timezone.utc)
    for e in earned:
        cred = cred_map.get(e["credential_key"])
        if not cred:
            continue
        expired = False
        if e.get("expires_at"):
            try:
                expired = datetime.fromisoformat(e["expires_at"]) < now
            except Exception:
                expired = False
        result.append({**cred, **e, "expired": expired})
    # show unearned too for discovery
    earned_keys = {e["credential_key"] for e in earned}
    unearned = [c for c in CREDENTIALS if c["key"] not in earned_keys]
    return {"earned": result, "available": unearned}


@api_router.get("/credentials/{key}/manifest.json")
async def credential_manifest(key: str):
    """OpenBadges v2 BadgeClass manifest (public)."""
    cred = next((c for c in CREDENTIALS if c["key"] == key), None)
    if not cred:
        raise HTTPException(404, "Credential not found")
    backend_url = os.environ.get('PUBLIC_BACKEND_URL', '')
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "BadgeClass",
        "id": f"{backend_url}/api/credentials/{key}/manifest.json",
        "name": cred["name"],
        "description": cred["description"],
        "image": cred.get("image") or "https://customer-assets.emergentagent.com/job_apprentice-academy/artifacts/zqurn9jd_WAI%20Logo.jpg",
        "criteria": {"narrative": cred["evidence"]},
        "issuer": {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Profile",
            "id": f"{backend_url}/api/issuer.json",
            "name": "W.A.I. — Workforce Apprentice Institute",
            "url": "https://workforceapprenticeinstitute.org",
        },
        "tags": cred.get("tags", []),
    }


@api_router.get("/credentials/assertion/{assertion_id}.json")
async def credential_assertion(assertion_id: str):
    """OpenBadges v2 Assertion (public, for verifiers)."""
    uc = await db.user_credentials.find_one({"id": assertion_id}, {"_id": 0})
    if not uc:
        raise HTTPException(404, "Assertion not found")
    user_doc = await db.users.find_one({"id": uc["user_id"]}, {"_id": 0, "password_hash": 0})
    cred = next((c for c in CREDENTIALS if c["key"] == uc["credential_key"]), None)
    if not cred or not user_doc:
        raise HTTPException(404, "Not found")
    backend_url = os.environ.get('PUBLIC_BACKEND_URL', '')
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "type": "Assertion",
        "id": f"{backend_url}/api/credentials/assertion/{assertion_id}.json",
        "recipient": {"type": "email", "hashed": False, "identity": user_doc["email"]},
        "issuedOn": uc["earned_at"],
        "expires": uc.get("expires_at"),
        "badge": f"{backend_url}/api/credentials/{cred['key']}/manifest.json",
        "verification": {"type": "HostedBadge"},
    }


@api_router.post("/portfolio/publish")
async def publish_portfolio(body: PortfolioPublishReq, user: User = Depends(current_user)):
    existing = await db.portfolios.find_one({"user_id": user.id}, {"_id": 0})
    slug = existing.get("slug") if existing else None
    if not slug and body.publish:
        slug = f"{user.full_name.lower().replace(' ', '-')}-{user.id[:8]}"
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
    update = {
        "user_id": user.id,
        "slug": slug if body.publish else None,
        "bio": body.bio,
        "published": bool(body.publish),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.portfolios.update_one(
        {"user_id": user.id},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    return {"slug": slug, "published": bool(body.publish)}


async def build_portfolio(user_doc: dict) -> dict:
    user_id = user_doc["id"]
    await award_credentials(user_id)

    mod_progress = await db.progress.find({"user_id": user_id}, {"_id": 0}).to_list(500)
    completed_mods = []
    for p in mod_progress:
        if p.get("status") == "completed":
            mod = await db.modules.find_one({"slug": p["module_slug"]}, {"_id": 0})
            if mod:
                completed_mods.append({
                    "slug": mod["slug"],
                    "title": mod["title"],
                    "hours": mod["hours"],
                    "score": p.get("quiz_score"),
                    "completed_at": p.get("completed_at"),
                })

    lab_subs = await db.lab_submissions.find(
        {"user_id": user_id, "status": {"$in": ["passed", "approved"]}}, {"_id": 0}
    ).to_list(500)
    labs_detail = []
    for s in lab_subs:
        lab = await db.labs.find_one({"slug": s["lab_slug"]}, {"_id": 0})
        if lab:
            labs_detail.append({
                "slug": lab["slug"],
                "title": lab["title"],
                "track": lab["track"],
                "skill_points": lab.get("skill_points", 0),
                "hours": lab.get("hours", 0),
                "photo_url": s.get("photo_url"),
                "notes": s.get("notes"),
                "feedback": s.get("feedback"),
                "auto_score": s.get("auto_score"),
                "completed_at": s.get("reviewed_at") or s.get("created_at"),
            })

    # competencies
    comp_map = {c["key"]: {**c, "points": 0, "labs": 0, "badge_earned": False} for c in COMPETENCIES}
    for s in lab_subs:
        lab = await db.labs.find_one({"slug": s["lab_slug"]}, {"_id": 0})
        if lab:
            for k in lab.get("competencies", []):
                if k in comp_map:
                    comp_map[k]["points"] += lab.get("skill_points", 0)
                    comp_map[k]["labs"] += 1
    for c in comp_map.values():
        c["badge_earned"] = c["points"] >= 100

    creds = await db.user_credentials.find({"user_id": user_id}, {"_id": 0}).to_list(200)
    cred_by_key = {c["key"]: c for c in CREDENTIALS}
    creds_detail = []
    for c in creds:
        cred = cred_by_key.get(c["credential_key"])
        if cred:
            creds_detail.append({**cred, **c})

    port = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})

    hours = sum(m["hours"] for m in completed_mods) + sum(l["hours"] for l in labs_detail)
    skill_points = sum(c["points"] for c in comp_map.values())

    return {
        "user": {
            "id": user_doc["id"],
            "full_name": user_doc["full_name"],
            "email": user_doc["email"],
            "associate": user_doc.get("associate"),
        },
        "bio": port.get("bio") if port else None,
        "share_slug": port.get("slug") if port and port.get("published") else None,
        "stats": {
            "hours": hours,
            "skill_points": skill_points,
            "modules_completed": len(completed_mods),
            "labs_passed": len(labs_detail),
            "credentials_earned": len(creds_detail),
            "badges_earned": sum(1 for c in comp_map.values() if c["badge_earned"]),
        },
        "modules": completed_mods,
        "labs": labs_detail,
        "credentials": creds_detail,
        "competencies": list(comp_map.values()),
    }


@api_router.get("/portfolio/me")
async def my_portfolio(user: User = Depends(current_user)):
    user_doc = await db.users.find_one({"id": user.id}, {"_id": 0, "password_hash": 0})
    return await build_portfolio(user_doc)


@api_router.get("/portfolio/public/{slug}")
async def public_portfolio(slug: str):
    port = await db.portfolios.find_one({"slug": slug, "published": True}, {"_id": 0})
    if not port:
        raise HTTPException(404, "Portfolio not found or not public")
    user_doc = await db.users.find_one({"id": port["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(404, "User not found")
    data = await build_portfolio(user_doc)
    # strip email for public view
    data["user"].pop("email", None)
    return data


@api_router.get("/portfolio/export.pdf")
async def portfolio_pdf(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    user_doc = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(401, "User not found")

    data = await build_portfolio(user_doc)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    w, h = letter

    def header():
        c.setFillColor(colors.HexColor("#0B203F"))
        c.rect(0, h - 1.3 * inch, w, 1.3 * inch, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#FFD100"))
        c.rect(0, h - 1.38 * inch, w, 0.08 * inch, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(0.6 * inch, h - 0.55 * inch, "W.A.I. — WORKFORCE APPRENTICE INSTITUTE")
        c.setFont("Helvetica", 9)
        c.drawString(0.6 * inch, h - 0.8 * inch, "LCE-WAI Partner Program  ·  Apprentice Portfolio")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(0.6 * inch, h - 1.1 * inch, data["user"]["full_name"])
        c.setFont("Helvetica", 10)
        right = f"Hours: {data['stats']['hours']}  ·  Points: {data['stats']['skill_points']}"
        c.drawRightString(w - 0.6 * inch, h - 1.1 * inch, right)

    def section(y, title):
        c.setFillColor(colors.HexColor("#0B203F"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.6 * inch, y, title.upper())
        c.setStrokeColor(colors.HexColor("#1E5BA8"))
        c.setLineWidth(2)
        c.line(0.6 * inch, y - 4, 0.6 * inch + 1.1 * inch, y - 4)

    header()
    y = h - 1.7 * inch
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica", 10)
    if data.get("bio"):
        c.drawString(0.6 * inch, y, data["bio"][:120])
        y -= 0.25 * inch

    def text_line(txt, bold=False, size=10):
        nonlocal y
        if y < 1 * inch:
            c.showPage()
            header()
            y = h - 1.7 * inch
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(0.7 * inch, y, txt[:95])
        y -= 0.22 * inch

    section(y, "Credentials & Badges")
    y -= 0.3 * inch
    for cr in data["credentials"]:
        text_line(f"• {cr['name']}  [{cr['category'].upper()}]", bold=True)
        text_line(f"   Earned {cr['earned_at'][:10]}" + (f"  ·  Expires {cr['expires_at'][:10]}" if cr.get("expires_at") else ""))
    if not data["credentials"]:
        text_line("  (none yet)")

    y -= 0.15 * inch
    section(y, "Competency Matrix")
    y -= 0.3 * inch
    for cmp in data["competencies"]:
        mark = "✓" if cmp["badge_earned"] else " "
        text_line(f" [{mark}] {cmp['name']}  —  {cmp['points']} pts  ({cmp['labs']} labs)")

    y -= 0.15 * inch
    section(y, "Modules Completed")
    y -= 0.3 * inch
    for m in data["modules"]:
        text_line(f"• {m['title']}  —  {m['hours']}h  ({int(m['score']) if m.get('score') else 0}%)")

    y -= 0.15 * inch
    section(y, "Labs Passed")
    y -= 0.3 * inch
    for l in data["labs"]:
        text_line(f"• {l['title']}  [{l['track'].upper()}]  —  {l['skill_points']} pts")

    # footer
    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(w / 2, 0.4 * inch, '"Whatever you do, work at it with all your heart." — Colossians 3:23')

    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=portfolio-{user_doc['id'][:8]}.pdf"},
    )


app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
