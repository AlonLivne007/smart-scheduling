"""
not in use for now
Pydantic schemas for the Rank model.

These schemas define the structure of data used for API requests and responses
related to the Rank entity. They allow the FastAPI application to validate and
serialize data between the client (frontend) and the database layer.

"""
from typing import Optional

from pydantic import BaseModel


class RankBase(BaseModel):
    """
    Base schema containing common fields shared by all Rank operations.
    """
    rank_name: str
    rank_is_manager: bool = False


class RankCreate(RankBase):
    """
    Schema used when creating a new Rank record.
    """
    pass


class RankUpdate(BaseModel):
    """
    Schema used when updating an existing Rank.
    """
    rank_name: Optional[str] = None
    rank_is_manager: Optional[bool] = None


class RankRead(RankBase):
    """
    Schema used for returning Rank data in API responses.
    Includes the unique identifier of the Rank.
    """
    rank_id: int

    class Config:
        orm_mode = True
