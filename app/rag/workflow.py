"""
LangGraph Agentic RAG workflow for the Enterprise IT Support Copilot.

Decision flow:
  START
    └─ route_question
         ├─ direct   → direct_answer → END
         └─ kb       → retrieve_kb
                           └─ grade_kb
                                ├─ good  → generate_from_kb → END
                                └─ weak  → search_web
                                               └─ grade_web
                                                    ├─ good  → generate_from_web → END
                                                    ├─ weak (retries left) → rewrite_query → retrieve_kb
                                                    └─ weak (no retries)   → insufficient → END

LLM provider : Groq (langchain-groq)
"""
import logging
from typing import Literal

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from app.core.config import get_settings
from app.rag.state import AgentState, RouteDecision, EvidenceGrade
from app.rag.vectorstore import get_retriever

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Lazy singletons so the app starts without hitting paid APIs ────────────────
_llm = None
_web_search = None


def llm() -> ChatGroq:
    """Return a cached Groq ChatLLM."""
    global _llm
    if _llm is None:
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        _llm = ChatGroq(
            model=settings.groq_model,
            temperature=0,
            api_key=settings.groq_api_key,
        )
    return _llm


def web_search_tool():
    """Return a cached Tavily search wrapper. Raises if key is missing."""
    global _web_search
    if _web_search is None:
        if not settings.tavily_api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Add it to your .env file."
            )
        # Import here so the app boots without tavily installed for unit tests.
        from tavily import TavilyClient  # type: ignore
        _web_search = TavilyClient(api_key=settings.tavily_api_key)
    return _web_search


# ── State helper ──────────────────────────────────────────────────────────────

def add_trace(state: AgentState, message: str) -> list[str]:
    return [*state.get("trace", []), message]


# ── Graph nodes ───────────────────────────────────────────────────────────────

def route_question(state: AgentState) -> dict:
    """Classify the question: 'kb' for IT support; 'direct' for greetings."""
    router = llm().with_structured_output(RouteDecision, method="json_mode")
    decision: RouteDecision = router.invoke(
        f"""You route messages for an enterprise IT support assistant.
Use "kb" for questions about company IT policies, VPN, password reset, MFA,
laptop setup, software access, security, email, devices, troubleshooting,
or any technology support topic.
Use "direct" ONLY for greetings, thanks, or casual chat that needs no company knowledge.
Question: {state['question']}
Return valid JSON exactly like {{"route":"kb"}} or {{"route":"direct"}}."""
    )
    route = decision.route
    logger.info("Router decision: %s", route)
    return {
        "source_used": route,
        "trace": add_trace(state, f"Router -> {route.upper()}"),
    }


def route_after_router(state: AgentState) -> Literal["retrieve_kb", "direct_answer"]:
    return "retrieve_kb" if state["source_used"] == "kb" else "direct_answer"


def retrieve_kb(state: AgentState) -> dict:
    """Search Pinecone private knowledge base for relevant chunks."""
    try:
        docs = get_retriever().invoke(state["current_query"])
    except Exception as exc:
        logger.warning("KB retrieval failed: %s", exc)
        docs = []
    logger.info("KB retrieval: %d chunks", len(docs))
    return {
        "kb_docs": docs,
        "trace": add_trace(state, f"Private KB retrieval -> {len(docs)} chunks"),
    }


def grade_kb(state: AgentState) -> dict:
    """Grade whether private KB evidence is sufficient to answer the question."""
    if not state["kb_docs"]:
        return {
            "kb_grade": "weak",
            "trace": add_trace(state, "KB evidence grade -> WEAK (no documents retrieved)"),
        }
    grader = llm().with_structured_output(EvidenceGrade, method="json_mode")
    context = "\n\n".join(
        f"Source: {d.metadata.get('source', 'unknown')}\n{d.page_content}"
        for d in state["kb_docs"]
    )
    grade: EvidenceGrade = grader.invoke(
        f"""You grade evidence quality for an enterprise IT support assistant.
Question: {state['question']}
Private company KB evidence:
{context}
Return "good" if the evidence contains relevant procedures, policies, or information that help answer the question.
Return "weak" ONLY if the evidence is completely irrelevant, lacks helpful information, or fails to address the topic.
Return valid JSON exactly like {{"grade":"good"}} or {{"grade":"weak"}}."""
    )
    logger.info("KB grade: %s", grade.grade)
    return {
        "kb_grade": grade.grade,
        "trace": add_trace(state, f"KB evidence grade -> {grade.grade.upper()}"),
    }


def after_kb(state: AgentState) -> Literal["generate_from_kb", "search_web"]:
    return "generate_from_kb" if state["kb_grade"] == "good" else "search_web"


def search_web(state: AgentState) -> dict:
    """Use Tavily to search the public web when private KB is insufficient."""
    try:
        tool = web_search_tool()
        result = tool.search(
            query=state["current_query"],
            max_results=5,
            include_answer=True,
        )
        lines: list[str] = []
        citations: list[dict] = []

        if isinstance(result, dict):
            if result.get("answer"):
                lines.append("Search answer: " + result["answer"])
            for item in result.get("results", []):
                title = item.get("title", "")
                url = item.get("url", "")
                content = item.get("content", "")
                lines.append(f"Title: {title}\nURL: {url}\nContent: {content}")
                citations.append({"title": title or url, "url": url, "type": "web"})
        else:
            lines.append(str(result))

        web_text = "\n\n".join(lines)
        logger.info("Web search returned %d citations.", len(citations))
        return {
            "web_results": web_text,
            "citations": citations,
            "source_used": "web",
            "trace": add_trace(state, f"Web fallback -> Tavily search ({len(citations)} results)"),
        }

    except Exception as exc:
        logger.warning("Web search failed: %s", exc)
        return {
            "web_results": "",
            "citations": [],
            "source_used": "web",
            "trace": add_trace(state, f"Web fallback -> Tavily search FAILED: {type(exc).__name__}"),
        }


def grade_web(state: AgentState) -> dict:
    """Grade whether web search evidence is sufficient."""
    if not state.get("web_results"):
        return {
            "web_grade": "weak",
            "trace": add_trace(state, "Web evidence grade -> WEAK (no web results)"),
        }
    grader = llm().with_structured_output(EvidenceGrade, method="json_mode")
    grade: EvidenceGrade = grader.invoke(
        f"""Question: {state['question']}
Web evidence:
{state['web_results']}
Return "good" if the evidence is sufficient and directly relevant.
Otherwise return "weak".
Return valid JSON exactly like {{"grade":"good"}} or {{"grade":"weak"}}."""
    )
    logger.info("Web grade: %s", grade.grade)
    return {
        "web_grade": grade.grade,
        "trace": add_trace(state, f"Web evidence grade -> {grade.grade.upper()}"),
    }


def after_web(
    state: AgentState,
) -> Literal["generate_from_web", "rewrite_query", "insufficient"]:
    if state["web_grade"] == "good":
        return "generate_from_web"
    if state["retry_count"] < settings.max_retries:
        return "rewrite_query"
    return "insufficient"


def rewrite_query(state: AgentState) -> dict:
    """Rewrite the query to improve retrieval on the next attempt."""
    rewritten: str = llm().invoke(
        f"""Rewrite this IT support question for better private knowledge retrieval
and vendor web search. Preserve the user's intent, add useful technical keywords,
do NOT answer the question, return only the improved query text.
Original question: {state['question']}"""
    ).content.strip()
    logger.info("Query rewritten to: %s", rewritten)
    return {
        "current_query": rewritten,
        "retry_count": state["retry_count"] + 1,
        "trace": add_trace(state, f"Query rewrite (attempt {state['retry_count'] + 1}) -> {rewritten}"),
    }


def generate_from_kb(state: AgentState) -> dict:
    """Generate a grounded answer from private KB evidence."""
    context = "\n\n".join(
        f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}"
        for d in state["kb_docs"]
    )
    answer: str = llm().invoke(
        f"""You are an enterprise IT support copilot for NovaRetail.
Answer ONLY from the private company knowledge base excerpts below.
Be concise, actionable, and safe. Present steps clearly when they exist.
Do NOT invent policy details or URLs not mentioned in the sources.
State that this answer is based on the company's private knowledge base.

Question: {state['question']}

Private KB:
{context}"""
    ).content

    # Build citations from retrieved document metadata.
    citations: list[dict] = []
    seen: set[str] = set()
    for d in state["kb_docs"]:
        src = d.metadata.get("source", "Private KB")
        if src not in seen:
            seen.add(src)
            citations.append({
                "title": src.split("/")[-1].split("\\")[-1],
                "url": None,
                "type": "private_kb",
                "document_id": src,
            })

    return {
        "answer": answer,
        "source_used": "private_kb",
        "citations": citations,
        "trace": add_trace(state, "Answer generation -> PRIVATE KB"),
    }


def generate_from_web(state: AgentState) -> dict:
    """Generate a grounded answer from web search evidence."""
    answer: str = llm().invoke(
        f"""You are an enterprise IT support copilot for NovaRetail.
The private company knowledge base did not contain sufficient information.
Answer ONLY from the web evidence below.
IMPORTANT: Clearly state this is external web information that may need validation
by the IT team before changing company-managed systems.
Do NOT invent information not present in the evidence.

Question: {state['question']}

Web evidence:
{state['web_results']}"""
    ).content

    return {
        "answer": answer,
        "source_used": "web_search",
        "trace": add_trace(state, "Answer generation -> WEB SEARCH"),
    }


def direct_answer(state: AgentState) -> dict:
    """Handle greetings and simple conversational messages directly."""
    answer: str = llm().invoke(
        f"Respond briefly and naturally as a friendly IT support assistant: {state['question']}"
    ).content
    return {
        "answer": answer,
        "source_used": "direct",
        "citations": [],
        "trace": add_trace(state, "Direct response -> no retrieval needed"),
    }


def insufficient(state: AgentState) -> dict:
    """Return a transparent insufficient-evidence response."""
    return {
        "answer": (
            "I could not find enough reliable evidence in the company knowledge base "
            "or external web search to answer your question confidently.\n\n"
            "Please contact the IT Help Desk directly:\n"
            "• Email: helpdesk@novaretail.com\n"
            "• Phone: ext. 4357 (HELP)\n"
            "• Ticket portal: https://helpdesk.novaretail.internal\n\n"
            "Provide as much detail as possible (error messages, device model, OS version)."
        ),
        "source_used": "insufficient_evidence",
        "citations": [],
        "trace": add_trace(state, "Stopped -> insufficient reliable evidence after retry limit"),
    }


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    # Add all nodes.
    for name, fn in {
        "route_question": route_question,
        "retrieve_kb": retrieve_kb,
        "grade_kb": grade_kb,
        "search_web": search_web,
        "grade_web": grade_web,
        "rewrite_query": rewrite_query,
        "generate_from_kb": generate_from_kb,
        "generate_from_web": generate_from_web,
        "direct_answer": direct_answer,
        "insufficient": insufficient,
    }.items():
        graph.add_node(name, fn)

    # Wire the graph.
    graph.add_edge(START, "route_question")
    graph.add_conditional_edges(
        "route_question",
        route_after_router,
        {"retrieve_kb": "retrieve_kb", "direct_answer": "direct_answer"},
    )
    graph.add_edge("retrieve_kb", "grade_kb")
    graph.add_conditional_edges(
        "grade_kb",
        after_kb,
        {"generate_from_kb": "generate_from_kb", "search_web": "search_web"},
    )
    graph.add_edge("search_web", "grade_web")
    graph.add_conditional_edges(
        "grade_web",
        after_web,
        {
            "generate_from_web": "generate_from_web",
            "rewrite_query": "rewrite_query",
            "insufficient": "insufficient",
        },
    )
    graph.add_edge("rewrite_query", "retrieve_kb")
    graph.add_edge("generate_from_kb", END)
    graph.add_edge("generate_from_web", END)
    graph.add_edge("direct_answer", END)
    graph.add_edge("insufficient", END)

    return graph.compile()


# Compiled graph — built once at module import time.
agent_graph = build_graph()


def ask(question: str) -> AgentState:
    """Entry point: run the agentic workflow for a given question."""
    initial: AgentState = {
        "question": question,
        "current_query": question,
        "kb_docs": [],
        "web_results": "",
        "kb_grade": "",
        "web_grade": "",
        "answer": "",
        "source_used": "",
        "retry_count": 0,
        "trace": [],
        "citations": [],
    }
    return agent_graph.invoke(initial)
