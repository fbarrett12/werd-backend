from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID

class WordCreate(BaseModel):
    text: str = Field(min_length=1, max_length=120)
    definition: str = Field(min_length=1, max_length=2000)
    part_of_speech: Optional[str] = Field(default=None, max_length=32)

class WordOut(BaseModel):
    id: UUID
    text: str
    definition: str
    part_of_speech: Optional[str] = None
    difficulty: Optional[int] = None
    approved: bool
    source: str

    model_config = ConfigDict(from_attributes=True)

    
