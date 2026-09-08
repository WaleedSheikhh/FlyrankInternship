from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class BookInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    price_gbp: float
    description: Optional[str] = None


class Category(str, Enum):
    fiction = "fiction"
    nonfiction = "nonfiction"
    poetry = "poetry"
    childrens = "childrens"
    other = "other"


class EnrichmentOutput(BaseModel):
    category: Category
    summary: str = Field(..., max_length=200)
    quality_flags: List[str] = []