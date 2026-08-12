from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config import BASE_DIR
from app.database import init_db
from app.routers import admin, chat

app = FastAPI(
    title="Course FAQ & Syllabus Chatbot API",
    description="Plug-and-Play AI Chatbot Widget backend powered by RAG, ChromaDB & Gemini 3.6 Flash",
    version="1.0.0"
)

# CORS configuration - Allow all origins so widget can be embedded anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Include API Routers
app.include_router(admin.router)
app.include_router(chat.router)

# Mount Static Directories for Admin Portal and Embeddable Widget
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True, parents=True)
(static_dir / "admin").mkdir(exist_ok=True, parents=True)
(static_dir / "widget").mkdir(exist_ok=True, parents=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def root():
    """Redirect root path to Admin Dashboard."""
    return RedirectResponse(url="/static/admin/index.html")
