"""Conversation domain models."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Actor(BaseModel):
    """Actor identity used for messages."""

    name: str = Field(min_length=1)
    email: str = Field(min_length=3)


class MessageCreate(BaseModel):
    """Payload for creating a new message."""

    content: str = Field(min_length=1)
    actor: Actor


class MessageRecord(BaseModel):
    """Stored conversation message."""

    id: int
    content: str
    actor_name: str
    actor_email: str
    created_at: datetime

    @property
    def display_actor(self) -> str:
        return f"{self.actor_name} <{self.actor_email}>"


def utcnow() -> datetime:
    """Return timezone-aware UTC now timestamp."""

    return datetime.now(timezone.utc)
