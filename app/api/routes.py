"""
FastAPI route handlers for the IT Support Copilot.

Endpoints:
  GET  /api/health   – service health and configuration status
  POST /api/chat     – run the agentic RAG workflow
  POST /api/ingest   – admin-protected document upload and indexing
"""
import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Header
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.rag.workflow import ask
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file, chunk_documents, SUPPORTED, MAX_FILE_SIZE_BYTES
from app.services.audit import write_audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
settings = get_settings()


# ── Request / response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000, description="The user's IT support question")


class Citation(BaseModel):
    title: str
    url: str | None = None
    type: str = "private_kb"
    document_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    source_used: str
    citations: list[dict]
    trace: list[str]
    retry_count: int
    status: str


# ── Health endpoint ───────────────────────────────────────────────────────────

@router.get("/health")
def health():
    """Return service status. Does not expose secrets."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "llm_provider": "groq",
        "llm_model": settings.groq_model,
        "embedding_model": settings.embedding_model,
        "groq_configured": bool(settings.groq_api_key),
        "pinecone_configured": bool(settings.pinecone_api_key),
        "tavily_configured": bool(settings.tavily_api_key),
        "admin_key_set": settings.admin_api_key != "change-me",
    }


# ── Chat endpoint ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """Run the agentic RAG workflow and return a structured response."""
    start_ms = int(time.time() * 1000)
    try:
        result = ask(payload.question)
        duration_ms = int(time.time() * 1000) - start_ms

        write_audit(
            question=payload.question,
            source_used=result.get("source_used", "unknown"),
            trace=result.get("trace", []),
            kb_grade=result.get("kb_grade", ""),
            web_grade=result.get("web_grade", ""),
            retry_count=result.get("retry_count", 0),
            status="success",
            duration_ms=duration_ms,
        )

        return {
            "answer": result.get("answer", ""),
            "source_used": result.get("source_used", "unknown"),
            "citations": result.get("citations", []),
            "trace": result.get("trace", []),
            "retry_count": result.get("retry_count", 0),
            "status": "success",
        }

    except Exception as exc:
        logger.error("Chat endpoint error: %s", exc, exc_info=True)
        write_audit(
            question=payload.question,
            source_used="error",
            trace=[f"Error: {type(exc).__name__}"],
            status="error",
        )
        # Do not expose raw exception details to the client.
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request. Please try again.",
        ) from exc


# ── Ingest endpoint ───────────────────────────────────────────────────────────

@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    x_admin_key: str = Header(default=""),
):
    """
    Admin-protected endpoint to upload and index a company document.
    Requires X-Admin-Key header matching ADMIN_API_KEY in .env.
    """
    # Authenticate using constant-time comparison to avoid timing attacks.
    import hmac
    if not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key.")

    # Validate file type.
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {', '.join(sorted(SUPPORTED))}",
        )

    # Read file content.
    content = await file.read()

    # Validate file size.
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is 20 MB.",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Generate a safe server-side filename (no path traversal).
    safe_name = Path(filename).name
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / safe_name

    # Write to disk.
    dest.write_bytes(content)
    logger.info("Uploaded file saved to %s (%d bytes)", dest, len(content))

    # Load, chunk, embed, and index.
    try:
        docs = load_file(dest)
        chunks = chunk_documents(docs)
        if not chunks:
            raise ValueError("No text content could be extracted from the document.")
        ids = add_documents(chunks)
    except ValueError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        dest.unlink(missing_ok=True)
        logger.error("Ingestion failed for %s: %s", safe_name, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Indexing failed. Check server logs for details.",
        ) from exc

    return {
        "message": "Document indexed successfully.",
        "file": safe_name,
        "chunks": len(chunks),
        "vectors_created": len(ids),
    }
