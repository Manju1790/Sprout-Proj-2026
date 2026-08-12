import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, save_course_metadata, get_active_course, get_unresolved_questions, get_analytics_summary
from app.rag_engine import index_document, query_rag_engine
from sample_data.create_sample_syllabus import generate_sample_syllabus_pdf

def test_full_pipeline():
    print("--------------------------------------------------")
    print("Testing Full System Pipeline")
    print("--------------------------------------------------")

    # 1. Init DB
    init_db()
    print("[OK] Database initialized.")

    # 2. Generate PDF
    sample_pdf = Path(__file__).resolve().parent / "sample_data" / "CS101_Syllabus.pdf"
    generate_sample_syllabus_pdf()
    assert sample_pdf.exists(), "Sample PDF not generated"
    print("[OK] Sample PDF generated.")

    # 3. Index PDF
    idx = index_document("default", sample_pdf)
    print(f"[OK] Indexed document into ChromaDB. Total Chunks: {idx['chunk_count']}")

    save_course_metadata(
        course_id="default",
        course_name=idx["course_name"],
        course_code=idx["course_code"],
        instructor=idx["instructor"],
        filename=sample_pdf.name,
        chunk_count=idx["chunk_count"],
        total_pages=idx["total_pages"]
    )
    
    course = get_active_course("default")
    assert course is not None, "Course metadata missing"
    print(f"[OK] Course Metadata stored: {course['course_name']} ({course['course_code']})")

    # 4. RAG Query Test 1: Known Syllabus Question
    q1 = "When is Assignment 2 due?"
    res1 = query_rag_engine("default", q1)
    print(f"\nQuestion 1: {q1}")
    print(f"Answer snippet: {res1['answer'][:150]}...")
    print(f"Sources: {res1['sources']}")
    print(f"Is Fallback: {res1['is_fallback']}")

    # 5. RAG Query Test 2: Unmentioned Policy (Triggers Unresolved Question Fallback)
    q2 = "What brand of coffee does the professor drink?"
    res2 = query_rag_engine("default", q2)
    print(f"\nQuestion 2: {q2}")
    print(f"Answer snippet: {res2['answer'][:150]}...")
    print(f"Is Fallback: {res2['is_fallback']}")

    # Log to DB
    from app.database import log_chat_interaction
    log_chat_interaction("default", q1, res1["answer"], res1["is_fallback"], ", ".join(res1["sources"]))
    log_chat_interaction("default", q2, res2["answer"], res2["is_fallback"], "")

    # Analytics check
    stats = get_analytics_summary("default")
    print(f"\n[OK] Analytics Check: Total Queries = {stats['total_queries']}, Resolution Rate = {stats['resolution_rate']}%")

    unresolved = get_unresolved_questions("default")
    print(f"[OK] Unresolved Questions Count = {len(unresolved)}")

    print("--------------------------------------------------")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    test_full_pipeline()
