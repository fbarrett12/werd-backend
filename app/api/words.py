from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.db.deps import get_db
from app.models.word import Word
from app.schemas.word import WordCreate, WordOut
from app.core.normalize import normalize_word

router = APIRouter(prefix="/api/words", tags=["words"])

@router.post("", response_model=WordOut, status_code=201)
def create_word(payload: WordCreate, db: Session = Depends(get_db)):
    normalized = normalize_word(payload.text)

    existing = db.execute(select(Word).where(Word.text_normalized == normalized)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Word already exists")

    word = Word(
        text=payload.text.strip(),
        text_normalized=normalized,
        definition=payload.definition.strip(),
        part_of_speech=payload.part_of_speech,
        difficulty=1,
        approved=True,
        source="user",
        times_seen=0,
        times_correct=0,
        times_incorrect=0,
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return word

@router.get("", response_model=list[WordOut])
def list_words(
    q: Optional[str] = Query(default=None, description="Search in word text"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Word).where(Word.approved == True)  # noqa: E712
    if q:
        stmt = stmt.where(Word.text.ilike(f"%{q.strip()}%"))
    stmt = stmt.order_by(Word.text.asc()).limit(limit).offset(offset)

    return list(db.execute(stmt).scalars().all())

@router.get("/random", response_model=list[WordOut])
def random_words(
    count: int = Query(default=1, ge=1, le=20),
    difficulty: Optional[int] = Query(default=None, ge=1, le=10),
    db: Session = Depends(get_db),
):
    stmt = select(Word).where(Word.approved == True)  # noqa: E712
    if difficulty is not None:
        stmt = stmt.where(Word.difficulty == difficulty)

    # Postgres random sampling
    stmt = stmt.order_by(Word.id).limit(1000)  # small guard; we’ll improve later
    words = list(db.execute(stmt).scalars().all())

    # simple fallback: just return first N; we’ll upgrade to ORDER BY random() next
    return words[:count]
