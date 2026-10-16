from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings, BASE_DIR
from app.core.logging import configure_logging
from app.services.audit import init_db


configure_logging()
settings = get_settings()
init_db()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Enterprise IT Support Agentic RAG Copilot for NovaRetail",
)

# CORS — restrict to same origin in production; allow localhost for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.app_name},
    )
