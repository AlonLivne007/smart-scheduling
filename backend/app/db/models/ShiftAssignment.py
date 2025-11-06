from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class ShiftAssignmentModel(Base):
    """
    Represents an assignment of a user to a specific planned shift
    in a specific role (e.g., 'Waiter', 'Bartender').

    Each record = 1 employee in 1 shift with 1 role.
    """

    __tablename__ = "shift_assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)

    # FK to PlannedShiftModel
    planned_shift_id = Column(
        Integer,
        ForeignKey("planned_shifts.planned_shift_id", ondelete="CASCADE"),
        nullable=False
    )

    # FK to UserModel
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    # FK to RoleModel (what role the user plays in this shift)
    role_id = Column(
        Integer,
        ForeignKey("roles.role_id"),
        nullable=False
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
    )

    def __repr__(self):
        return (
            f"<ShiftAssignment("
            f"shift_id={self.planned_shift_id}, "
            f"user_id={self.user_id}, "
            f"role_id={self.role_id})>"
        )
