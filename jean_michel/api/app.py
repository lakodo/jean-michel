"""FastAPI app exposing conversation endpoints and HTML UI."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from jean_michel.git_state import compare_refs, inspect_repository, list_reference_candidates
from jean_michel.metrics import CoverageComputationError
from jean_michel.services import ConversationService, MetricsService
from jean_michel.settings import find_repo_root, get_db_path, get_default_api_port, get_repo_identity
from jean_michel.storage import DuckDBConversationStore


def create_app() -> FastAPI:
    app = FastAPI(title="Jean-Michel Conversation")
    store = DuckDBConversationStore(get_db_path())
    service = ConversationService(store)
    metrics = MetricsService(store)
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
    def home_page(
        request: Request,
        limit: int = 100,
        tab: str = "conversation",
        base_ref: str = "",
        target_ref: str = "",
        coverage_error: str = "",
        coverage_command_error: str = "",
    ):
        context = _base_context(limit=limit, tab=tab)
        if tab == "repository":
            try:
                context["repo_snapshot"] = inspect_repository(repo_root)
                context["repo_error"] = None
            except RuntimeError:
                context["repo_snapshot"] = None
                context["repo_error"] = "Unable to inspect repository state."
            context["coverage_by_short"] = metrics.coverage_by_short_commit()
            context["coverage_error"] = coverage_error
            context["coverage_command"] = metrics.get_coverage_command()
            context["coverage_command_error"] = coverage_command_error
            context["messages"] = []
            context["compare_result"] = None
            context["compare_error"] = None
            context["ref_candidates"] = []
            context["base_ref"] = ""
            context["target_ref"] = ""
        elif tab == "compare":
            context["messages"] = []
            context["repo_snapshot"] = None
            context["repo_error"] = None
            context["base_ref"] = base_ref
            context["target_ref"] = target_ref
            try:
                context["ref_candidates"] = list_reference_candidates(repo_root)
            except RuntimeError:
                context["ref_candidates"] = []

            if base_ref.strip() and target_ref.strip():
                try:
                    context["compare_result"] = compare_refs(repo_root, base_ref, target_ref)
                    context["compare_error"] = None
                except (RuntimeError, ValueError):
                    context["compare_result"] = None
                    context["compare_error"] = "Unable to compare these references."
            else:
                context["compare_result"] = None
                context["compare_error"] = None
            context["coverage_by_short"] = {}
            context["coverage_error"] = ""
            context["coverage_command"] = ""
            context["coverage_command_error"] = ""
        else:
            context["messages"] = service.list_messages(limit=limit)
            context["repo_snapshot"] = None
            context["repo_error"] = None
            context["compare_result"] = None
            context["compare_error"] = None
            context["ref_candidates"] = []
            context["base_ref"] = ""
            context["target_ref"] = ""
            context["coverage_by_short"] = {}
            context["coverage_error"] = ""
            context["coverage_command"] = ""
            context["coverage_command_error"] = ""

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

    @app.get("/api/compare")
    def compare_commits(base_ref: str, target_ref: str):
        return compare_refs(repo_root, base_ref, target_ref)

    @app.get("/api/references")
    def list_references(q: str = "", limit: int = 25):
        return list_reference_candidates(repo_root, query=q, limit=limit)

    @app.get("/api/coverage")
    def get_coverage(ref: str):
        try:
            report = metrics.get_cached_coverage_for_ref(ref)
        except CoverageComputationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if report is None:
            raise HTTPException(status_code=404, detail="Coverage not cached for this ref")
        return report

    @app.post("/coverage/compute")
    def compute_coverage(ref: str = Form(...), force: bool = Form(False)):
        try:
            metrics.compute_coverage_for_ref(ref=ref, force=force)
            return RedirectResponse(url="/?tab=repository", status_code=303)
        except CoverageComputationError as exc:
            message = quote_plus(str(exc))
            return RedirectResponse(url=f"/?tab=repository&coverage_error={message}", status_code=303)

    @app.post("/coverage/command")
    def set_coverage_command(command: str = Form(...)):
        try:
            metrics.set_coverage_command(command)
            return RedirectResponse(url="/?tab=repository", status_code=303)
        except ValueError as exc:
            message = quote_plus(str(exc))
            return RedirectResponse(url=f"/?tab=repository&coverage_command_error={message}", status_code=303)

    @app.post("/api/coverage/compute")
    def compute_coverage_api(ref: str = Form(...), force: bool = Form(False)):
        try:
            report, cached = metrics.compute_coverage_for_ref(ref=ref, force=force)
            return {"cached": cached, "report": report}
        except CoverageComputationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/coverage/command")
    def get_coverage_command_api():
        return {"command": metrics.get_coverage_command()}

    @app.post("/api/coverage/command")
    def set_coverage_command_api(command: str = Form(...)):
        try:
            return {"command": metrics.set_coverage_command(command)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
