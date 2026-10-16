import pytest
from app.rag.state import RouteDecision, EvidenceGrade
from app.services.ingestion import chunk_documents
from langchain_core.documents import Document
from app.services.audit import init_db, write_audit, _connect

def test_route_decision_model():
    r1 = RouteDecision(route="kb")
    assert r1.route == "kb"
    r2 = RouteDecision(route="direct")
    assert r2.route == "direct"
    with pytest.raises(Exception):
        RouteDecision(route="invalid_route")

def test_evidence_grade_model():
    g1 = EvidenceGrade(grade="good")
    assert g1.grade == "good"
    g2 = EvidenceGrade(grade="weak")
    assert g2.grade == "weak"
    with pytest.raises(Exception):
        EvidenceGrade(grade="medium")

def test_chunking_documents():
    docs = [
        Document(
            page_content="This is a test document containing text to split. " * 30,
            metadata={"source": "test.md"}
        )
    ]
    chunks = chunk_documents(docs)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.metadata.get("source") == "test.md"
        assert len(chunk.page_content) > 0

def test_audit_logging():
    init_db()
    write_audit(
        question="How do I reset my password?",
        source_used="private_kb",
        trace=["Router -> KB", "Answer -> PRIVATE KB"],
        kb_grade="good",
        status="success",
        duration_ms=450,
    )
    con = _connect()
    row = con.execute("SELECT question, source_used, kb_grade FROM query_audit ORDER BY id DESC LIMIT 1").fetchone()
    con.close()
    assert row is not None
    assert row[0] == "How do I reset my password?"
    assert row[1] == "private_kb"
    assert row[2] == "good"
