from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_active_course, log_chat_interaction
from app.rag_engine import query_rag_engine

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class QuestionRequest(BaseModel):
    question: str
    course_id: Optional[str] = "default"

@router.post("/query")
async def chat_query(payload: QuestionRequest):
    question_text = payload.question.strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    course_id = payload.course_id or "default"
    
    # Query RAG Engine
    res = query_rag_engine(course_id=course_id, question=question_text)
    
    answer = res["answer"]
    is_fallback = res["is_fallback"]
    sources = ", ".join(res["sources"]) if res["sources"] else ""

    # Log interaction & log unresolved if fallback
    log_chat_interaction(
        course_id=course_id,
        question=question_text,
        answer=answer,
        is_fallback=is_fallback,
        sources=sources
    )

    return {
        "status": "success",
        "answer": answer,
        "is_fallback": is_fallback,
        "sources": res["sources"]
    }

@router.get("/suggested-questions")
async def get_suggested_questions(course_id: str = "default"):
    course = get_active_course(course_id)
    course_name = course["course_name"] if course else "this course"
    
    return {
        "suggested_questions": [
            f"When is Assignment 2 due in {course_name}?",
            "What is the policy for late submissions?",
            "What are the instructor and TA office hours?",
            "How is the final grade calculated?",
            "Where can I find the required textbook?"
        ]
    }

@router.get("/widget-config")
async def get_widget_config(course_id: str = "default"):
    course = get_active_course(course_id)
    if not course:
        return {
            "configured": False,
            "title": "Course Assistant",
            "subtitle": "Ask any question about syllabus & policies"
        }
    return {
        "configured": True,
        "title": f"{course['course_code']} Assistant" if course['course_code'] else course['course_name'],
        "subtitle": f"Instructor: {course['instructor']}",
        "course_name": course['course_name'],
        "syllabus_filename": course['syllabus_filename']
    }
