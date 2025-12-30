from __future__ import annotations

import re
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.word import Word


def normalize(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


SEED_WORDS = [
    ("finna", "About to do something.", 2),
    ("deadass", "Seriously; genuinely; not joking.", 2),
    ("cap", "To lie or exaggerate; 'no cap' means no lie.", 2),
    ("bet", "Okay; agreed; for sure.", 1),
    ("slaps", "Is really good (usually music/food).", 1),
    ("sus", "Suspicious; questionable.", 1),
    ("lit", "Exciting; fun; excellent.", 1),
    ("ate", "Did extremely well; crushed it.", 2),
    ("drag", "To criticize heavily; roast.", 2),
    ("shade", "Subtle disrespect or criticism.", 2),
]


def main() -> None:
    db = SessionLocal()
    try:
        created = 0
        skipped = 0

        for text, definition, difficulty in SEED_WORDS:
            norm = normalize(text)
            exists = db.execute(select(Word).where(Word.text_normalized == norm)).scalar_one_or_none()
            if exists:
                skipped += 1
                continue

            db.add(
                Word(
                    text=text.strip(),
                    text_normalized=norm,
                    definition=definition.strip(),
                    difficulty=difficulty,
                    approved=True,
                    source="seed",
                )
            )
            created += 1

        db.commit()
        print(f"Seed complete. Created={created}, Skipped={skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
