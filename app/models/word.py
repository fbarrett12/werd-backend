import uuid
from sqlalchemy import String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.db.base import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    text: Mapped[str] = mapped_column(String(120), nullable=False)
    text_normalized: Mapped[str] = mapped_column(String(140), nullable=False, unique=True, index=True)

    definition: Mapped[str] = mapped_column(Text, nullable=False)

    part_of_speech: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1", default=1)

    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    source: Mapped[str] = mapped_column(String(32), nullable=False, default="import")

    times_seen: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    times_correct: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    times_incorrect: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
