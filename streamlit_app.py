"""
IT Support Agentic RAG Copilot - Streamlit UI.
Powered by Groq (LLM), Pinecone (Vector DB), HuggingFace (Local 384-dim Embeddings), and Tavily (Web Search).
"""
import time
import sqlite3
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.core.config import get_settings
from app.rag.workflow import ask
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file, chunk_documents, SUPPORTED
from app.services.audit import init_db, write_audit

settings = get_settings()
init_db()

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IT Support Agentic RAG Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Enterprise IT Support Agentic RAG Copilot — Powered by Groq, Pinecone, LangGraph & Tavily"
    },
)

# ── Load CSS via st.html(Path) ────────────────────────────────────────────────
css_path = Path(__file__).parent / "static" / "css" / "streamlit.css"
if css_path.exists():
    st.html(css_path)


# ── Render Helpers ────────────────────────────────────────────────────────────
def _badge(src: str, ms: int = 0, rc: int = 0) -> str:
    cfg = {
        "private_kb": ("sb-k", "📚 Private KB"),
        "web_search": ("sb-w", "🌐 Web Search"),
        "direct": ("sb-d", "💬 Direct Response"),
        "insufficient_evidence": ("sb-e", "⚠️ Insufficient Evidence"),
    }
    css_class, label = cfg.get(src, ("sb-e", src.upper()))
    t = f'<span class="tc">⏱ {ms:,}ms</span>' if ms else ""
    r = f'<span class="rc">🔄 Rewritten ({rc})</span>' if rc else ""
    return f'<div class="sbr"><span class="sb {css_class}">{label}</span>{t}{r}</div>'


def _trace(steps: list[str]) -> str:
    if not steps:
        return ""
    items = []
    for s in steps:
        if "->" in s:
            node, action = s.split("->", 1)
            txt = f"{node.strip()} &rarr; <strong>{action.strip()}</strong>"
        else:
            txt = s
        items.append(
            f'<div class="tstep"><div class="tdot"><div class="tdi"></div></div>'
            f'<div class="ttxt">{txt}</div></div>'
        )
    return f'<div class="tcon">{"".join(items)}</div>'


def _citations(cits: list[dict]) -> str:
    if not cits:
        return ""
    pills = []
    for c in cits:
        ttl = c.get("title", "Document")[:40]
        is_web = c.get("type") == "web"
        ico = "🌐" if is_web else "📄"
        lbl = "Web" if is_web else "KB"
        url = c.get("url", "")
        if url:
            pills.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="cpill">'
                f'{ico} {ttl}<span class="ct">[{lbl}]</span></a>'
            )
        else:
            pills.append(
                f'<span class="cpill">{ico} {ttl}<span class="ct">[{lbl}]</span></span>'
            )
    return f'<div class="crow">{"".join(pills)}</div>'


# ── Session State Initialization ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "num_queries" not in st.session_state:
    st.session_state.num_queries = 0
    st.session_state.num_kb = 0
    st.session_state.num_web = 0
    st.session_state.total_ms = 0


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.html("""
    <div class="sb-brand">
        <div class="sb-brand-icon">🛡️</div>
        <div class="sb-brand-title">IT Support Agentic RAG Copilot</div>
        <div class="sb-brand-sub">Enterprise AI Assistant</div>
    </div>
    """)

    st.html('<div class="ss-t">⚡ Service Status</div>')
    gok = bool(settings.groq_api_key)
    pok = bool(settings.pinecone_api_key)
    tok = bool(settings.tavily_api_key)

    def status_card(lbl: str, val: str, ok: bool, color_override: str = None) -> str:
        dot_color = color_override or ("dg" if ok else "dr")
        return (
            f'<div class="sp">'
            f'<div class="dot {dot_color}"></div>'
            f'<span class="pl">{lbl}</span>'
            f'<span class="ps">{val}</span>'
            f'</div>'
        )

    model_short = settings.groq_model.split("/")[-1]
    status_html = (
        status_card("Groq LLM", model_short, gok)
        + status_card("Pinecone DB", settings.pinecone_index_name, pok)
        + status_card("Tavily Search", "enabled" if tok else "disabled", tok, None if tok else "da")
        + status_card("Embeddings", "384-dim local", True)
    )
    st.html(status_html)

    st.html('<div class="ss-t">📊 Session Metrics</div>')
    nq = st.session_state.num_queries
    nkb = st.session_state.num_kb
    nweb = st.session_state.num_web
    avg_speed = int(st.session_state.total_ms / nq) if nq > 0 else 0
    st.html(f"""
    <div class="mg">
        <div class="mc"><div class="mv">{nq}</div><div class="ml">Queries</div></div>
        <div class="mc"><div class="mv">{avg_speed}ms</div><div class="ml">Avg Speed</div></div>
        <div class="mc"><div class="mv">{nkb}</div><div class="ml">KB Hits</div></div>
        <div class="mc"><div class="mv">{nweb}</div><div class="ml">Web Hits</div></div>
    </div>
    """)

    st.html('<div class="ss-t">📚 Knowledge Base</div>')
    if st.button("📥  Index Sample IT Documents", use_container_width=True):
        with st.spinner("Ingesting & embedding sample documents into Pinecone..."):
            try:
                sd = Path(settings.sample_kb_dir)
                files = [p for p in sd.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]
                docs = []
                for f in files:
                    docs.extend(load_file(f))
                chunks = chunk_documents(docs)
                ids = add_documents(chunks)
                st.success(f"Indexed {len(ids)} chunks from {len(files)} docs into Pinecone!")
            except Exception as e:
                st.error(f"Indexing error: {e}")

    uf = st.file_uploader("Upload IT Document", type=["pdf", "docx", "txt", "md"], label_visibility="collapsed")
    if uf and st.button("⬆️  Index Uploaded Document", use_container_width=True):
        with st.spinner(f"Ingesting {uf.name}..."):
            try:
                ud = Path(settings.upload_dir)
                ud.mkdir(parents=True, exist_ok=True)
                tp = ud / uf.name
                with open(tp, "wb") as fh:
                    fh.write(uf.getbuffer())
                chunks = chunk_documents(load_file(tp))
                ids = add_documents(chunks)
                st.success(f"Indexed {len(ids)} chunks from '{uf.name}'!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.html('<div class="ss-t">📋 Recent Audit Log</div>')
    with st.expander("View Last 5 Queries"):
        try:
            con = sqlite3.connect(settings.audit_db_path)
            rows = con.execute(
                "SELECT created_at, question, source_used, duration_ms FROM query_audit ORDER BY id DESC LIMIT 5"
            ).fetchall()
            con.close()
            icons = {"private_kb": "📚", "web_search": "🌐", "direct": "💬"}
            if rows:
                for r in rows:
                    ico = icons.get(r[2], "❓")
                    ts = r[0][:16].replace("T", " ")
                    q_trunc = r[1][:45] + ("..." if len(r[1]) > 45 else "")
                    st.html(
                        f'<div style="font-size:0.7rem;color:#64748b;margin-top:0.4rem">{ts}</div>'
                        f'<div style="font-size:0.78rem;color:#cbd5e1;font-weight:600">{ico} {q_trunc}</div>'
                        f'<div style="font-size:0.68rem;color:#94a3b8;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:0.35rem">'
                        f'{r[2]} · {r[3] or 0}ms</div>'
                    )
            else:
                st.caption("No queries recorded yet.")
        except Exception as e:
            st.caption(f"Audit unavailable: {e}")

    st.html('<div class="ss-t">⚙️ Settings</div>')
    if st.button("🗑️  Clear Conversation History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.num_queries = 0
        st.session_state.num_kb = 0
        st.session_state.num_web = 0
        st.session_state.total_ms = 0
        st.rerun()


# ── MAIN AREA: Hero Banner ────────────────────────────────────────────────────
st.html("""
<div class="hero">
    <div class="hlogo">🛡️</div>
    <div class="htitle">IT Support <span>Agentic RAG Copilot</span></div>
    <div class="hsub">
        Autonomous enterprise support agent with self-corrective retrieval.
        Answers from your private company knowledge base first, verifies evidence quality with an LLM grader,
        falls back to Tavily web search when required, and provides end-to-end transparent decision reasoning.
    </div>
    <div class="htags">
        <span class="htag">⚡ LangGraph State Machine</span>
        <span class="htag">🌲 Pinecone Vector DB</span>
        <span class="htag">🚀 Groq LLM Inference</span>
        <span class="htag">⚖️ Self-Grading Evidence</span>
        <span class="htag">🌐 Tavily Web Search</span>
        <span class="htag">🔒 Private KB Grounding</span>
    </div>
</div>
""")

# ── MAIN AREA: Interactive Pipeline Architecture ──────────────────────────────
st.html("""
<div class="pipeline">
    <div class="pst"><div class="pi pi-r">🧭</div><div class="plbl">1. ROUTER</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-k">🗄️</div><div class="plbl">2. RETRIEVE KB</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-g">⚖️</div><div class="plbl">3. GRADE KB</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-w">🌐</div><div class="plbl">4. WEB FALLBACK</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-g">⚖️</div><div class="plbl">5. GRADE WEB</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-r">🔄</div><div class="plbl">6. REWRITE QUERY</div></div>
    <div class="parr">›</div>
    <div class="pst"><div class="pi pi-n">✨</div><div class="plbl">7. GENERATE</div></div>
</div>
""")

# ── MAIN AREA: Suggested Questions ───────────────────────────────────────────
st.html('<div class="stitle">💡 Quick IT Support Inquiries</div>')
prompt_from_button = None

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔒 Connect to NovaSecure VPN?", use_container_width=True):
        prompt_from_button = "How do I connect to the company NovaSecure VPN on Windows and macOS?"
with col2:
    if st.button("🔑 Password policy requirements?", use_container_width=True):
        prompt_from_button = "What are the company password policy requirements and self-service reset steps?"
with col3:
    if st.button("💻 Request new laptop hardware?", use_container_width=True):
        prompt_from_button = "What is the procedure to request a new laptop or hardware peripheral?"
with col4:
    if st.button("🌍 Latest Microsoft Teams features?", use_container_width=True):
        prompt_from_button = "What are the latest Microsoft Teams features released in 2024?"

col5, col6, col7, col8 = st.columns(4)
with col5:
    if st.button("🚨 Report lost or stolen device?", use_container_width=True):
        prompt_from_button = "How do I report a lost or stolen company laptop?"
with col6:
    if st.button("📱 Setup Microsoft Authenticator?", use_container_width=True):
        prompt_from_button = "How do I set up Microsoft Authenticator MFA on my mobile phone?"
with col7:
    if st.button("🖨️ Install office network printer?", use_container_width=True):
        prompt_from_button = "Steps to install a network printer in the NovaRetail office?"
with col8:
    if st.button("👋 Hello! What can you do?", use_container_width=True):
        prompt_from_button = "Hello, what IT support tasks can you help me with?"

st.html("<div style='height: 12px;'></div>")

# ── MAIN AREA: Chat History ───────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role, avatar="🛡️" if role == "assistant" else "👤"):
        if role == "assistant" and msg.get("source_used"):
            st.html(_badge(msg["source_used"], msg.get("duration_ms", 0), msg.get("retry_count", 0)))
        st.markdown(msg["content"])
        if role == "assistant":
            trace = msg.get("trace", [])
            citations = msg.get("citations", [])
            if trace or citations:
                with st.expander("🔍 Agentic Trace & Citations", expanded=False):
                    if trace:
                        st.html('<div style="font-size:0.72rem;font-weight:700;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.4rem">LangGraph Decision Path</div>')
                        st.html(_trace(trace))
                    if citations:
                        st.html('<div style="font-size:0.72rem;font-weight:700;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;margin:0.7rem 0 0.4rem">Retrieved Sources</div>')
                        st.html(_citations(citations))

# ── MAIN AREA: Chat Input & Execution ─────────────────────────────────────────
user_query = st.chat_input("Ask your IT support question — VPN, passwords, MFA, hardware, security...")
active_prompt = prompt_from_button or user_query

if active_prompt:
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(active_prompt)

    # 2. Assistant execution
    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Processing question through Agentic RAG workflow..."):
            t0 = time.perf_counter()
            try:
                res = ask(active_prompt)
                duration_ms = int((time.perf_counter() - t0) * 1000)
                
                answer = res.get("answer", "No response generated.")
                source_used = res.get("source_used", "unknown")
                trace = res.get("trace", [])
                citations = res.get("citations", [])
                kb_grade = res.get("kb_grade", "")
                web_grade = res.get("web_grade", "")
                retry_count = res.get("retry_count", 0)

                # Update session metrics
                st.session_state.num_queries += 1
                st.session_state.total_ms += duration_ms
                if source_used == "private_kb":
                    st.session_state.num_kb += 1
                elif source_used == "web_search":
                    st.session_state.num_web += 1

                # Record audit entry in SQLite
                write_audit(
                    question=active_prompt,
                    source_used=source_used,
                    trace=trace,
                    kb_grade=kb_grade,
                    web_grade=web_grade,
                    retry_count=retry_count,
                    status="success",
                    duration_ms=duration_ms,
                )

                # Render response
                st.html(_badge(source_used, duration_ms, retry_count))
                st.markdown(answer)

                if trace or citations:
                    with st.expander("🔍 Agentic Trace & Citations", expanded=True):
                        if trace:
                            st.html('<div style="font-size:0.72rem;font-weight:700;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.4rem">LangGraph Decision Path</div>')
                            st.html(_trace(trace))
                        if citations:
                            st.html('<div style="font-size:0.72rem;font-weight:700;color:#64748b;letter-spacing:0.06em;text-transform:uppercase;margin:0.7rem 0 0.4rem">Retrieved Sources</div>')
                            st.html(_citations(citations))

                # Save assistant message to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "source_used": source_used,
                    "trace": trace,
                    "citations": citations,
                    "duration_ms": duration_ms,
                    "retry_count": retry_count,
                })

            except Exception as exc:
                st.error(f"⚠️ Error executing agent workflow: {exc}")
                write_audit(
                    question=active_prompt,
                    source_used="error",
                    trace=[str(exc)],
                    status="error",
                )
