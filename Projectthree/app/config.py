import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMADB_DIR = DATA_DIR / "chromadb"
DB_PATH = DATA_DIR / "syllabus.db"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
UPLOADS_DIR.mkdir(exist_ok=True, parents=True)
CHROMADB_DIR.mkdir(exist_ok=True, parents=True)
SAMPLE_DATA_DIR.mkdir(exist_ok=True, parents=True)

# API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_MODEL = "gemini-3.6-flash"
VECTOR_COLLECTION_NAME = "course_syllabi"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
