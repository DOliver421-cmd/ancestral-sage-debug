from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from pathlib import Path

app = FastAPI(title="Ancestral Sage", description="Ancient wisdom for modern seekers")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# EMBEDDED DATA - NO IMPORTS NEEDED
MODULES = [
    "ancient_wisdom",
    "spiritual_guidance", 
    "ancestral_knowledge",
    "meditation_practices",
    "herbal_remedies",
    "dream_interpretation",
    "chakra_balancing",
    "crystal_healing"
]

def quiz_for(module_name):
    if module_name not in MODULES:
        return {"error": f"Module '{module_name}' not found"}
    
    return {
        "module": module_name,
        "questions": [
            f"What is the essence of {module_name.replace('_', ' ')}?",
            f"How can {module_name.replace('_', ' ')} be applied in daily life?",
            f"What are the key principles of {module_name.replace('_', ' ')}?",
            f"What historical context shapes {module_name.replace('_', ' ')}?"
        ],
        "difficulty": "beginner",
        "total_questions": 4
    }

@app.get("/")
async def root():
    return {"message": "Welcome to Ancestral Sage API", "status": "active"}

@app.get("/api/modules")
async def get_modules():
    return {"modules": MODULES}

@app.get("/api/quiz/{module_name}")
async def get_quiz(module_name: str):
    if module_name not in MODULES:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    
    quiz_data = quiz_for(module_name)
    return quiz_data

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ancestral-sage"}

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path == "":
            return FileResponse("frontend/index.html")
        return FileResponse(f"frontend/{full_path}")
