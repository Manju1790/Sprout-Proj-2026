# Plug-and-Play AI Course FAQ & Syllabus Chatbot Widget 🎓🤖

An intelligent, zero-friction full-stack RAG solution for university professors and TAs. Instructors simply drop a course syllabus (PDF/CSV/TXT) into the Admin Dashboard, and the system automatically parses the document, builds a ChromaDB vector index, and generates a 1-line HTML embed snippet to add a 24/7 AI Chat Assistant to any course website or LMS.

---

## 🌟 Key Features

1. **Drop-in Configuration**: Upload syllabus PDF via drag-and-drop. System extracts sections, chunks text, generates embeddings, and saves into ChromaDB.
2. **1-Line Embed Snippet**:
   ```html
   <script src="http://localhost:8000/static/widget/embed.js" data-course-id="default"></script>
   ```
3. **Grounded RAG (Gemini 3.6 Flash)**: Answers student questions strictly based on syllabus content (office hours, grading policy, assignment deadlines, late policies).
4. **Unresolved Question Tracker**: Automatically logs student questions when syllabus info is missing or low-confidence into SQLite, giving teachers insight into policy gaps.
5. **Glassmorphism UI**: Modern aesthetic Admin Dashboard & floating chat bubble widget with dark/light themes, typing indicators, and citations.

---

## 🏗️ Full-Stack Architecture

- **Frontend**: Glassmorphism Admin Upload & Analytics Portal + Embeddable Floating Chat Widget (`embed.js`).
- **Backend API**: FastAPI (`app/main.py`, `app/routers/admin.py`, `app/routers/chat.py`).
- **RAG & Vector Core**: ChromaDB (persistent vector DB), PyPDF, Gemini 3.6 Flash (`google-genai`).
- **Database**: SQLite (`data/syllabus.db`) for course metadata, chat logs, and unresolved student questions.

---

## 🚀 Quickstart Guide

### 1. Environment & Setup
The project runs inside `venv` in the `Projectthree` directory:
```bash
# Navigate to Projectthree directory
cd Projectthree

# Virtual environment is located at ./venv
# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 2. Start Application Server
Run the one-click launcher:
```bash
python run.py
```
This will:
- Initialize SQLite database & directories.
- Generate sample syllabus `CS101_Syllabus.pdf`.
- Build ChromaDB vector search index.
- Launch FastAPI on `http://localhost:8000`.
- Open Admin Dashboard in your default browser (`http://localhost:8000/static/admin/index.html`).

---

## 🧪 Testing the Widget

1. Open Admin Portal: `http://localhost:8000/static/admin/index.html`
2. Test Chat Simulator tab or visit Sample Course Page: `http://localhost:8000/static/test_embed.html`
3. Ask sample questions:
   - *"When is Assignment 2 due?"*
   - *"What is the policy for late submissions?"*
   - *"What are Dr. Jenkins' office hours?"*
   - *"How is the final grade calculated?"*
