"""Conversation use cases."""

from __future__ import annotations

from jean_michel.git_identity import resolve_default_actor
from jean_michel.models import Actor, MessageCreate, MessageRecord
from jean_michel.storage import DuckDBConversationStore


class ConversationService:
    """Service to send and read conversation messages."""

    def __init__(self, store: DuckDBConversationStore):
        self.store = store

    def send_message(self, content: str, actor: Actor | None = None) -> MessageRecord:
        normalized_content = content.strip()
        if not normalized_content:
            raise ValueError("Message content cannot be empty")

        message = MessageCreate(content=normalized_content, actor=actor or resolve_default_actor())
        return self.store.insert_message(message)

    def list_messages(self, limit: int = 100) -> list[MessageRecord]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return self.store.list_messages(limit=limit)

    def default_actor(self) -> Actor:
        return resolve_default_actor()
