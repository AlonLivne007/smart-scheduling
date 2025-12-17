"""
System-wide constraints model definition.

This module defines the SystemConstraints ORM model representing global work rules
that apply to all employees (e.g., max hours per week, minimum rest hours).
"""

from sqlalchemy import Column, Integer, Float, Boolean, Enum as SqlEnum, UniqueConstraint, Index
from app.db.session import Base
import enum


class SystemConstraintType(enum.Enum):
    """
    Enumeration for system-wide constraint types.

    Values:
        MAX_HOURS_PER_WEEK: Maximum allowed working hours per week
        MIN_HOURS_PER_WEEK: Minimum target working hours per week
        MAX_CONSECUTIVE_DAYS: Maximum consecutive working days
        MIN_REST_HOURS: Minimum rest hours between shifts
        MAX_SHIFTS_PER_WEEK: Maximum number of shifts per week
        MIN_SHIFTS_PER_WEEK: Minimum number of shifts per week
    """

    MAX_HOURS_PER_WEEK = "MAX_HOURS_PER_WEEK"
    MIN_HOURS_PER_WEEK = "MIN_HOURS_PER_WEEK"
    MAX_CONSECUTIVE_DAYS = "MAX_CONSECUTIVE_DAYS"
    MIN_REST_HOURS = "MIN_REST_HOURS"
    MAX_SHIFTS_PER_WEEK = "MAX_SHIFTS_PER_WEEK"
    MIN_SHIFTS_PER_WEEK = "MIN_SHIFTS_PER_WEEK"


class SystemConstraintsModel(Base):
    """
    System-wide constraints model.

    This table stores global work rules that apply to all employees.

    Attributes:
        constraint_id: Primary key identifier
        constraint_type: Type of constraint (enum)
        constraint_value: Numeric limit value for the constraint
        is_hard_constraint: True if must be satisfied, False if soft/preferred
    """

    __tablename__ = "system_constraints"

    constraint_id = Column(Integer, primary_key=True, index=True)

    constraint_type = Column(
        SqlEnum(SystemConstraintType, name="systemconstrainttype"),
        nullable=False,
        unique=True,
    )

    # Use Float to support both integer-like values (e.g., shifts) and fractional hours
    constraint_value = Column(Float, nullable=False)

    is_hard_constraint = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("constraint_type", name="uq_system_constraint_type"),
        Index("idx_system_constraints_type", "constraint_type"),
    )

    def __repr__(self):
        """String representation of the system constraint."""
        return (
            f"<SystemConstraint("
            f"id={self.constraint_id}, "
            f"type='{self.constraint_type.value}', "
            f"value={self.constraint_value}, "
            f"is_hard={self.is_hard_constraint})>"
        )


