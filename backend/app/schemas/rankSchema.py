"""
Rank schema definitions.

This module defines Pydantic schemas for rank data validation and serialization.
Currently not in active use but available for future hierarchy management.
"""

from typing import Optional

from pydantic import BaseModel


class RankBase(BaseModel):
    """Base rank schema with common fields."""
    rank_name: str
    rank_is_manager: bool = False


class RankCreate(RankBase):
    """Schema for creating new ranks."""
    pass


class RankUpdate(BaseModel):
    """Schema for updating existing ranks."""
    rank_name: Optional[str] = None
    rank_is_manager: Optional[bool] = None


class RankRead(RankBase):
    """Schema for rank data in API responses."""
    rank_id: int

    class Config:
        orm_mode = True
