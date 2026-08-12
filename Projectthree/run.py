import os
import sys
import webbrowser
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, save_course_metadata, get_active_course
from app.rag_engine import index_document
from sample_data.create_sample_syllabus import generate_sample_syllabus_pdf

def setup_and_launch():
    print("=" * 60)
    print("🚀 Initializing Plug-and-Play AI Course FAQ Chatbot")
    print("=" * 60)

    # 1. Initialize DB
    init_db()
    print("✅ SQLite Database initialized at data/syllabus.db")

    # 2. Ensure Sample Syllabus PDF exists
    sample_pdf = Path(__file__).resolve().parent / "sample_data" / "CS101_Syllabus.pdf"
    if not sample_pdf.exists():
        print("📄 Generating sample CS101 syllabus PDF...")
        generate_sample_syllabus_pdf()

    # 3. Auto-index sample syllabus if DB is empty
    if sample_pdf.exists() and not get_active_course("default"):
        print("🔍 Indexing sample CS101 syllabus into ChromaDB...")
        try:
            res = index_document("default", sample_pdf)
            save_course_metadata(
                course_id="default",
                course_name=res["course_name"],
                course_code=res["course_code"],
                instructor=res["instructor"],
                filename=sample_pdf.name,
                chunk_count=res["chunk_count"],
                total_pages=res["total_pages"]
            )
            print(f"✅ Indexed {res['chunk_count']} vector chunks for CS101!")
        except Exception as e:
            print(f"⚠️ Indexing notice: {e}")

    print("\n🌐 Starting FastAPI Server on http://localhost:8000...")
    print("📊 Admin Dashboard: http://localhost:8000/static/admin/index.html")
    print("🧪 Test Embed Page: http://localhost:8000/static/test_embed.html")
    print("=" * 60)

    # Open browser automatically after short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000/static/admin/index.html")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Uvicorn server
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    setup_and_launch()
