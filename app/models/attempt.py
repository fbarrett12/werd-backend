import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # The correct word for this question
    word_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("words.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    # "def_to_word" | "word_to_def"
    mode: Mapped[str] = mapped_column(String(24), nullable=False)

    # What was shown on top (word or definition)
    prompt: Mapped[str] = mapped_column(String, nullable=False)

    # The 4 cards shown.
    # Store as a JSON array of objects like:
    # [
    #   {"word_id": "...", "text": "finna"},
    #   {"word_id": "...", "text": "deadass"},
    #   ...
    # ]
    # or for word_to_def:
    # [
    #   {"word_id": "...", "definition": "about to..."},
    #   ...
    # ]
    choices: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)

    selected_word_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("words.id", ondelete="RESTRICT"),
        nullable=True,
    )

    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
