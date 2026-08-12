import os
import sys
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Proxy wrapper for sqlite3 to bypass ChromaDB version check on Windows Python 3.8
class Sqlite3Proxy:
    def __init__(self, target):
        self._target = target
        self.sqlite_version_info = (3, 35, 0)
        self.sqlite_version = "3.35.0"
    def __getattr__(self, name):
        return getattr(self._target, name)

sys.modules['sqlite3'] = Sqlite3Proxy(sqlite3)

import pypdf

# Dual support for Gemini SDK
GENAI_MODE = None
try:
    from google import genai
    GENAI_MODE = "new"
except ImportError:
    try:
        import google.generativeai as genai_old
        GENAI_MODE = "old"
    except ImportError:
        GENAI_MODE = None

from app.config import CHROMADB_DIR, GEMINI_API_KEY, DEFAULT_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from app.database import get_setting

import chromadb
chroma_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))

def get_vector_collection(course_id: str = "default"):
    """Get or create a ChromaDB collection for a specific course."""
    collection_name = f"course_{re.sub(r'[^a-zA-Z0-9_-]', '_', course_id)}"
    return chroma_client.get_or_create_collection(name=collection_name)

def get_effective_api_key() -> str:
    """Retrieve API key from DB settings or environment variables."""
    key = get_setting("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        key = GEMINI_API_KEY
    return key

def call_gemini_api(prompt: str) -> Optional[str]:
    """Helper to call Gemini API across SDK versions."""
    api_key = get_effective_api_key()
    if not api_key:
        return None

    try:
        if GENAI_MODE == "new":
            client = genai.Client(api_key=api_key)
            response = client.interactions.create(
                model=DEFAULT_MODEL,
                input=prompt
            )
            return response.output_text
        elif GENAI_MODE == "old":
            import google.generativeai as genai_old
            genai_old.configure(api_key=api_key)
            try:
                model = genai_old.GenerativeModel("gemini-3.6-flash")
                res = model.generate_content(prompt)
                return res.text
            except Exception:
                model = genai_old.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(prompt)
                return res.text
    except Exception as e:
        print(f"Gemini API invocation error: {e}")
        return None

def parse_pdf(file_path: Path) -> Tuple[str, List[Dict[str, Any]], int]:
    """
    Parses a PDF document into full text and structured page chunks.
    Returns (full_text, pages_data, total_pages).
    """
    reader = pypdf.PdfReader(str(file_path))
    pages_data = []
    full_text_builder = []
    
    total_pages = len(reader.pages)
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        page_text = page.extract_text() or ""
        clean_text = re.sub(r'\n+', '\n', page_text).strip()
        if clean_text:
            pages_data.append({
                "page": page_num,
                "text": clean_text
            })
            full_text_builder.append(f"--- PAGE {page_num} ---\n{clean_text}")

    full_text = "\n\n".join(full_text_builder)
    return full_text, pages_data, total_pages

def chunk_text(pages_data: List[Dict[str, Any]], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Splits page text into semantic chunks with metadata.
    """
    chunks = []
    chunk_id_counter = 0

    for page_info in pages_data:
        page_num = page_info["page"]
        text = page_info["text"]

        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        current_chunk = []
        current_length = 0
        current_heading = f"Page {page_num}"

        for p in paragraphs:
            if len(p) < 60 and (p.isupper() or p.endswith(':') or re.match(r'^(Module|Chapter|Section|Unit|Policy|Grading|Schedule|Office Hours)', p, re.I)):
                current_heading = p

            p_len = len(p)
            if current_length + p_len > chunk_size and current_chunk:
                chunk_str = "\n".join(current_chunk)
                chunk_id_counter += 1
                chunks.append({
                    "id": f"chunk_{page_num}_{chunk_id_counter}",
                    "text": chunk_str,
                    "metadata": {
                        "page": page_num,
                        "heading": current_heading
                    }
                })
                current_chunk = current_chunk[-1:] if current_chunk else []
                current_length = sum(len(c) for c in current_chunk)

            current_chunk.append(p)
            current_length += p_len

        if current_chunk:
            chunk_str = "\n".join(current_chunk)
            chunk_id_counter += 1
            chunks.append({
                "id": f"chunk_{page_num}_{chunk_id_counter}",
                "text": chunk_str,
                "metadata": {
                    "page": page_num,
                    "heading": current_heading
                }
            })

    return chunks

def index_document(course_id: str, file_path: Path) -> Dict[str, Any]:
    """
    Parses PDF, chunks text, creates ChromaDB vector store embeddings.
    """
    full_text, pages_data, total_pages = parse_pdf(file_path)
    chunks = chunk_text(pages_data)
    
    collection = get_vector_collection(course_id)
    
    existing = collection.get()
    existing_ids = existing.get("ids", [])
    if existing_ids:
        collection.delete(ids=existing_ids)

    if chunks:
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [f"{course_id}_{c['id']}" for c in chunks]

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    course_name = file_path.stem.replace("_", " ")
    course_code = "CS"
    instructor = "Course Instructor"

    extraction_prompt = f"""
    Analyze the following syllabus preview text and extract:
    1. Course Title (e.g. Introduction to Computer Science)
    2. Course Code (e.g. CS101)
    3. Instructor Name (e.g. Dr. Jane Smith)

    Syllabus Preview:
    {full_text[:2000]}

    Return output in exactly this format:
    COURSE_TITLE: <title>
    COURSE_CODE: <code>
    INSTRUCTOR: <instructor>
    """
    out = call_gemini_api(extraction_prompt)
    if out:
        title_match = re.search(r'COURSE_TITLE:\s*(.+)', out)
        code_match = re.search(r'COURSE_CODE:\s*(.+)', out)
        inst_match = re.search(r'INSTRUCTOR:\s*(.+)', out)

        if title_match and title_match.group(1).strip():
            course_name = title_match.group(1).strip()
        if code_match and code_match.group(1).strip():
            course_code = code_match.group(1).strip()
        if inst_match and inst_match.group(1).strip():
            instructor = inst_match.group(1).strip()

    return {
        "course_name": course_name,
        "course_code": course_code,
        "instructor": instructor,
        "chunk_count": len(chunks),
        "total_pages": total_pages
    }

def query_rag_engine(course_id: str, question: str) -> Dict[str, Any]:
    """
    Queries vector database for syllabus chunks, passes context to Gemini 3.6 Flash,
    and returns answer + citations + fallback flag.
    """
    collection = get_vector_collection(course_id)
    
    count = collection.count()
    if count == 0:
        return {
            "answer": "No syllabus document has been uploaded or indexed for this course yet. Please ask your instructor to upload the syllabus in the Admin Dashboard.",
            "is_fallback": True,
            "sources": []
        }

    results = collection.query(
        query_texts=[question],
        n_results=min(4, count)
    )

    retrieved_docs = results.get("documents", [[]])[0]
    retrieved_metas = results.get("metadatas", [[]])[0]

    if not retrieved_docs:
        return {
            "answer": "No matching syllabus sections were found for your question.",
            "is_fallback": True,
            "sources": []
        }

    context_blocks = []
    sources = []
    for doc, meta in zip(retrieved_docs, retrieved_metas):
        page = meta.get("page", "?")
        heading = meta.get("heading", "Syllabus Section")
        context_blocks.append(f"[Section: {heading} (Page {page})]\n{doc}")
        sources.append(f"{heading} (Page {page})")

    context_str = "\n\n".join(context_blocks)

    api_key = get_effective_api_key()
    if not api_key:
        return {
            "answer": f"**Gemini API Key missing.** Here are the relevant syllabus sections found for your question:\n\n{context_str}\n\n*Please configure your Gemini API Key in the Admin Dashboard to enable AI natural language responses.*",
            "is_fallback": False,
            "sources": list(set(sources))
        }

    rag_prompt = f"""
    You are an intelligent, friendly AI Course Assistant for a university class.
    Your task is to answer the student's question accurately based ONLY on the provided Syllabus Context.

    CRITICAL RULES:
    1. Base your answer STRICTLY on the facts present in the Syllabus Context.
    2. If the context does not explicitly contain the answer (e.g. an unmentioned deadline, policy, or detail), respond politely stating:
       "I couldn't find specific information regarding this in the uploaded syllabus. I've logged your question so the instructor can clarify it for you!"
    3. Include helpful formatting (bullet points, bold text for key dates or policies).
    4. Keep answers concise, clear, and reassuring.

    SYLLABUS CONTEXT:
    {context_str}

    STUDENT QUESTION:
    {question}

    ANSWER:
    """

    answer = call_gemini_api(rag_prompt)
    if not answer:
        return {
            "answer": f"Relevant syllabus context retrieved:\n\n{context_str}\n\n*(Could not connect to Gemini API. Please check your API key settings.)*",
            "is_fallback": True,
            "sources": list(set(sources))
        }

    fallback_indicators = [
        "couldn't find specific information",
        "not mentioned in the syllabus",
        "not specified in the syllabus",
        "does not mention",
        "logged your question"
    ]
    is_fallback = any(ind in answer.lower() for ind in fallback_indicators)

    return {
        "answer": answer.strip(),
        "is_fallback": is_fallback,
        "sources": list(set(sources)) if not is_fallback else []
    }
