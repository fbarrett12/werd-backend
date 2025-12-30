from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


QuizMode = Literal["def_to_word", "word_to_def"]


class SessionCreate(BaseModel):
    mode: QuizMode
    difficulty: int | None = Field(default=None, ge=1, le=10)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    mode: QuizMode
    difficulty: int | None
    score: int
    streak: int


class Choice(BaseModel):
    word_id: UUID
    text: str | None = None
    definition: str | None = None


class QuestionOut(BaseModel):
    attempt_id: UUID
    session_id: UUID
    mode: QuizMode
    prompt: str
    choices: list[Choice]


class AnswerIn(BaseModel):
    attempt_id: UUID
    selected_word_id: UUID


class AnswerOut(BaseModel):
    correct: bool
    correct_word_id: UUID
    correct_text: str
    correct_definition: str
    score: int
    streak: int
