"""
Rank model definition.

This module defines the Rank ORM model used to represent employee hierarchy levels
within the scheduling system. Each rank can optionally indicate whether it includes
managerial privileges.

"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Rank(Base):
    """
    Represents an employee rank (e.g., 'Manager', 'Junior', 'Trainee').

    Attributes:
        rank_id (int): Unique identifier for the rank.
        rank_name (str): Name of the rank.
        rank_is_manager (bool): Indicates whether this rank represents a managerial role.
        users (list[User]): Relationship to users holding this rank.
    """

    __tablename__ = "ranks"

    rank_id = Column(Integer, primary_key=True, index=True)
    rank_name = Column(String, unique=True, nullable=False)
    rank_is_manager = Column(Boolean, default=False)

    # One-to-many relationship: one Rank → many Users
    users = relationship("User", back_populates="rank")

    def __repr__(self):
        """Return a readable string representation of the Rank object."""
        return f"<Rank(name='{self.rank_name}', is_manager={self.rank_is_manager})>"
