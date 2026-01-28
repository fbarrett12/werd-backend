import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_device_id
from app.db.deps import get_db
from app.models.game_session import GameSession
from app.models.attempt import Attempt
from app.models.word import Word
from app.schemas.game import (
    SessionCreate,
    SessionOut,
    QuestionOut,
    Choice,
    AnswerIn,
    AnswerOut,
)

router = APIRouter(prefix="/api", tags=["game"])


def _get_random_word(db: Session, difficulty: int | None) -> Word:
    stmt = select(Word).where(Word.approved == True)  # noqa: E712
    if difficulty is not None:
        stmt = stmt.where(Word.difficulty == difficulty)
    # simple random for now; we can optimize later
    stmt = stmt.order_by(func.random()).limit(1)
    word = db.execute(stmt).scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="No words available for this filter")
    return word


def _get_distractors(db: Session, correct_id: UUID, difficulty: int | None, n: int = 3) -> list[Word]:
    stmt = select(Word).where(
        Word.approved == True,  # noqa: E712
        Word.id != correct_id,
    )
    if difficulty is not None:
        stmt = stmt.where(Word.difficulty == difficulty)

    stmt = stmt.order_by(func.random()).limit(n)
    return list(db.execute(stmt).scalars().all())


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate,
    device_id: UUID = Depends(get_device_id),
    db: Session = Depends(get_db),
):
    session = GameSession(
        device_id=device_id,
        mode=payload.mode,
        difficulty=payload.difficulty,
        score=0,
        streak=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/sessions/{session_id}/question", response_model=QuestionOut)
def create_question(
    session_id: UUID,
    device_id: UUID = Depends(get_device_id),
    db: Session = Depends(get_db),
):
    session = db.execute(select(GameSession).where(GameSession.id == session_id)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not your session")

    correct = _get_random_word(db, session.difficulty)
    distractors = _get_distractors(db, correct.id, session.difficulty, n=3)

    if len(distractors) < 3:
        raise HTTPException(status_code=400, detail="Not enough words to generate choices")

    words = [correct, *distractors]
    random.shuffle(words)

    # Build prompt + choices based on mode
    if session.mode == "def_to_word":
        prompt = correct.definition
        choices = [{"word_id": str(w.id), "text": w.text} for w in words]
    else:  # word_to_def
        prompt = correct.text
        choices = [{"word_id": str(w.id), "definition": w.definition} for w in words]

    attempt = Attempt(
        session_id=session.id,
        word_id=correct.id,
        mode=session.mode,
        prompt=prompt,
        choices=choices,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuestionOut(
        attempt_id=attempt.id,
        session_id=session.id,
        mode=session.mode,
        prompt=prompt,
        choices=[Choice(**c) for c in choices],
    )


@router.post("/sessions/{session_id}/answer", response_model=AnswerOut)
def submit_answer(
    session_id: UUID,
    payload: AnswerIn,
    device_id: UUID = Depends(get_device_id),
    db: Session = Depends(get_db),
):
    session = db.execute(select(GameSession).where(GameSession.id == session_id)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not your session")

    attempt = db.execute(
        select(Attempt).where(Attempt.id == payload.attempt_id, Attempt.session_id == session.id)
    ).scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found for this session")

    # Validate selected option is one of the stored choices
    try:
        choice_ids = {
            UUID(str(c["word_id"]))
            for c in attempt.choices
            if c.get("word_id") is not None
        }
    except (ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=500,
            detail="Corrupt attempt choices",
        )
    
    if payload.selected_word_id not in choice_ids:
        raise HTTPException(status_code=400, detail="Selected choice was not in the presented options")

    correct = payload.selected_word_id == attempt.word_id

    attempt.selected_word_id = payload.selected_word_id
    attempt.is_correct = correct

    if correct:
        session.score += 1
        session.streak += 1
    else:
        session.streak = 0

    correct_word = db.execute(select(Word).where(Word.id == attempt.word_id)).scalar_one()

    correct_word.times_seen += 1
    if correct:
        correct_word.times_correct += 1
    else:
        correct_word.times_incorrect += 1

    # Difficulty formula (simple + stable)
    # miss_rate in [0,1]. Map to [1..10] and add a little weight for volume.
    miss_rate = correct_word.times_incorrect / max(1, correct_word.times_seen)

    # Example mapping:
    # - 0% miss => 1
    # - 100% miss => 10
    computed = 1 + round(miss_rate * 9)

    # Require a minimum sample size before it can climb
    if correct_word.times_seen < 10:
        computed = min(computed, 3)

    correct_word.difficulty = max(1, min(10, computed))

    db.commit()

    return AnswerOut(
        correct=correct,
        correct_word_id=correct_word.id,
        correct_text=correct_word.text,
        correct_definition=correct_word.definition,
        score=session.score,
        streak=session.streak,
    )
