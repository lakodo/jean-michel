"""FastAPI app exposing conversation endpoints and HTML UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from jean_michel.git_state import inspect_repository
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

    def _base_context(limit: int, tab: str) -> dict[str, object]:
        actor = service.default_actor()
        return {
            "actor": actor,
            "limit": limit,
            "repo_name": repo_root.name,
            "repo_root": str(repo_root),
            "repo_identity": repo_identity,
            "db_path": str(db_path),
            "default_port": default_port,
            "active_tab": tab,
        }

    @app.get("/")
    def home_page(request: Request, limit: int = 100, tab: str = "conversation"):
        context = _base_context(limit=limit, tab=tab)
        if tab == "repository":
            try:
                context["repo_snapshot"] = inspect_repository(repo_root)
                context["repo_error"] = None
            except RuntimeError:
                context["repo_snapshot"] = None
                context["repo_error"] = "Unable to inspect repository state."
            context["messages"] = []
        else:
            context["messages"] = service.list_messages(limit=limit)
            context["repo_snapshot"] = None
            context["repo_error"] = None

        return templates.TemplateResponse(request, "conversation.html", context)

    @app.post("/messages")
    def create_message(content: str = Form(...)):
        service.send_message(content=content)
        return RedirectResponse(url="/?tab=conversation", status_code=303)

    @app.get("/api/messages")
    def list_messages(limit: int = 100):
        return service.list_messages(limit=limit)

    @app.get("/api/repository")
    def repository_state():
        return inspect_repository(repo_root)

    return app


app = create_app()
