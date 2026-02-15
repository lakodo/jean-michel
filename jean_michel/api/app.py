"""FastAPI app exposing conversation endpoints and HTML UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from jean_michel.services import ConversationService
from jean_michel.settings import find_repo_root, get_db_path, get_default_api_port, get_repo_identity
from jean_michel.storage import DuckDBConversationStore


def _build_service() -> ConversationService:
    db_path = get_db_path()
    store = DuckDBConversationStore(db_path)
    return ConversationService(store)


def create_app() -> FastAPI:
    app = FastAPI(title="Jean-Michel Conversation")
    service = _build_service()
    repo_root = find_repo_root()
    repo_identity = get_repo_identity(repo_root)
    db_path = get_db_path()
    default_port = get_default_api_port(repo_root)
    templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

    @app.get("/")
    def conversation_page(request: Request, limit: int = 100):
        messages = service.list_messages(limit=limit)
        actor = service.default_actor()
        return templates.TemplateResponse(
            request,
            "conversation.html",
            {
                "messages": messages,
                "actor": actor,
                "limit": limit,
                "repo_name": repo_root.name,
                "repo_root": str(repo_root),
                "repo_identity": repo_identity,
                "db_path": str(db_path),
                "default_port": default_port,
            },
        )

    @app.post("/messages")
    def create_message(content: str = Form(...)):
        service.send_message(content=content)
        return RedirectResponse(url="/", status_code=303)

    @app.get("/api/messages")
    def list_messages(limit: int = 100):
        return service.list_messages(limit=limit)

    return app


app = create_app()
