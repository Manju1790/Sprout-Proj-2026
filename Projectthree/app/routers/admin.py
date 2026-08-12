import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.config import UPLOADS_DIR, GEMINI_API_KEY
from app.database import (
    save_course_metadata, get_active_course, get_unresolved_questions,
    mark_unresolved_question_status, delete_unresolved_question,
    get_analytics_summary, set_setting, get_setting
)
from app.rag_engine import index_document

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class ApiKeyUpdate(BaseModel):
    api_key: str

class QuestionStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = ""

@router.post("/upload-syllabus")
async def upload_syllabus(
    file: UploadFile = File(...),
    course_id: str = Form("default"),
    custom_course_name: Optional[str] = Form(None)
):
    if not file.filename.lower().endswith(('.pdf', '.txt', '.csv')):
        raise HTTPException(status_code=400, detail="Only PDF, TXT, or CSV files are supported.")

    file_path = UPLOADS_DIR / f"{course_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Index document into ChromaDB & extract metadata
        idx_res = index_document(course_id=course_id, file_path=file_path)
        
        course_name = custom_course_name if custom_course_name else idx_res["course_name"]
        
        save_course_metadata(
            course_id=course_id,
            course_name=course_name,
            course_code=idx_res["course_code"],
            instructor=idx_res["instructor"],
            filename=file.filename,
            chunk_count=idx_res["chunk_count"],
            total_pages=idx_res["total_pages"]
        )

        return {
            "status": "success",
            "message": f"Successfully parsed and indexed '{file.filename}'!",
            "course": {
                "course_id": course_id,
                "course_name": course_name,
                "course_code": idx_res["course_code"],
                "instructor": idx_res["instructor"],
                "chunk_count": idx_res["chunk_count"],
                "total_pages": idx_res["total_pages"],
                "filename": file.filename
            }
        }
    except Exception as e:
        print(f"Upload processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/course")
async def get_course_info(course_id: str = "default"):
    course = get_active_course(course_id)
    if not course:
        return {
            "has_syllabus": False,
            "message": "No syllabus uploaded yet."
        }
    return {
        "has_syllabus": True,
        "course": course
    }

@router.get("/unresolved-questions")
async def list_unresolved_questions(course_id: str = "default"):
    questions = get_unresolved_questions(course_id)
    return {"unresolved_questions": questions}

@router.post("/unresolved-questions/{question_id}/status")
async def update_question_status(question_id: int, payload: QuestionStatusUpdate):
    mark_unresolved_question_status(question_id, payload.status, payload.notes or "")
    return {"status": "success", "message": "Updated question status."}

@router.delete("/unresolved-questions/{question_id}")
async def remove_unresolved_question(question_id: int):
    delete_unresolved_question(question_id)
    return {"status": "success", "message": "Question deleted."}

@router.get("/analytics")
async def get_analytics(course_id: str = "default"):
    summary = get_analytics_summary(course_id)
    return summary

@router.post("/settings/api-key")
async def update_api_key(payload: ApiKeyUpdate):
    set_setting("GEMINI_API_KEY", payload.api_key.strip())
    return {"status": "success", "message": "Gemini API Key updated successfully."}

@router.get("/settings/api-key")
async def get_api_key_status():
    stored_key = get_setting("GEMINI_API_KEY") or GEMINI_API_KEY
    is_configured = bool(stored_key and len(stored_key) > 10)
    masked = f"{stored_key[:6]}...{stored_key[-4:]}" if is_configured else "Not Configured"
    return {
        "configured": is_configured,
        "masked_key": masked
    }
