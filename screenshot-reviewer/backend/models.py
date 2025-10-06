from pydantic import BaseModel
from typing import List, Optional

class Screenshot(BaseModel):
    id: str
    path: str
    tags: List[str] = []
    summary: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0

class Category(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
