"""
Rank model definition.

This module defines the Rank ORM model representing employee hierarchy levels
within the organization. Each rank indicates whether it includes managerial
privileges. Currently not in active use.
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Rank(Base):
    """
    Rank model representing employee hierarchy levels.
    
    Attributes:
        rank_id: Primary key identifier
        rank_name: Name of the rank (unique)
        rank_is_manager: Managerial privileges flag
        users: Users with this rank
    """
    __tablename__ = "ranks"

    rank_id = Column(Integer, primary_key=True, index=True)
    rank_name = Column(String, unique=True, nullable=False)
    rank_is_manager = Column(Boolean, default=False)

    # One-to-many relationship with users
    users = relationship("User", back_populates="rank")

    def __repr__(self):
        """String representation of the rank."""
        return f"<Rank(name='{self.rank_name}', is_manager={self.rank_is_manager})>"
