"""
Shift assignment model definition.

This module defines the ShiftAssignment ORM model representing the assignment
of a user to a specific planned shift in a specific role. Each record represents
one employee assigned to one shift with one role (e.g., 'Waiter', 'Bartender').
"""

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class ShiftAssignmentModel(Base):
    """
    Shift assignment model representing a user assigned to a planned shift in a specific role.
    
    Attributes:
        assignment_id: Primary key identifier
        planned_shift_id: Foreign key to the planned shift
        user_id: Foreign key to the assigned user
        role_id: Foreign key to the role the user plays in this shift
        planned_shift: Relationship to the planned shift
        user: Relationship to the assigned user
        role: Relationship to the role
    """

    __tablename__ = "shift_assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)

    # FK to PlannedShiftModel
    planned_shift_id = Column(
        Integer,
        ForeignKey("planned_shifts.planned_shift_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK to UserModel
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK to RoleModel (what role the user plays in this shift)
    role_id = Column(
        Integer,
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Relationships
    planned_shift = relationship(
        "PlannedShiftModel",
        back_populates="assignments"
    )

    user = relationship(
        "UserModel",
        lazy="selectin"
    )

    role = relationship(
        "RoleModel",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("planned_shift_id", "user_id", name="uq_shift_user"),
        Index("idx_assignment_shift_role", "planned_shift_id", "role_id"),
    )

    def __repr__(self):
        """String representation of the shift assignment."""
        return (
            f"<ShiftAssignment("
            f"shift_id={self.planned_shift_id}, "
            f"user_id={self.user_id}, "
            f"role_id={self.role_id})>"
        )
