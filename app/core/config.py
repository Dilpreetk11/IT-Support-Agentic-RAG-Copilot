from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Enterprise IT Support Agentic RAG Copilot"
    app_env: str = "development"

    # ── LLM (Groq) ────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"   # High capability Groq model


    # ── Embeddings (local HuggingFace, no key needed) ─────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Vector database (Pinecone) ────────────────────────────────────────────
    pinecone_api_key: str = ""
    pinecone_index_name: str = "fde-it-support-rag"
    pinecone_namespace: str = "company-it-kb"

    # ── External search (Tavily) ──────────────────────────────────────────────
    tavily_api_key: str = ""

    # ── Admin / security ──────────────────────────────────────────────────────
    admin_api_key: str = "change-me"

    # ── Retrieval / workflow tuning ───────────────────────────────────────────
    top_k: int = 4
    max_retries: int = 1
    chunk_size: int = 900
    chunk_overlap: int = 120

    # ── Storage paths ─────────────────────────────────────────────────────────
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    sample_kb_dir: str = str(BASE_DIR / "data" / "sample_kb")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
