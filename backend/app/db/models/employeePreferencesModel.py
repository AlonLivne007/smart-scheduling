"""
Employee preferences model definition.

This module defines the EmployeePreferences ORM model representing employee shift
preferences. Employees can specify preferred shift templates, days of the week,
time ranges, and weight their preferences by importance. These preferences are
considered during schedule optimization.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Time, Float, Index, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class DayOfWeek(enum.Enum):
    """
    Enumeration for days of the week.
    
    Values:
        MONDAY: Monday
        TUESDAY: Tuesday
        WEDNESDAY: Wednesday
        THURSDAY: Thursday
        FRIDAY: Friday
        SATURDAY: Saturday
        SUNDAY: Sunday
    """
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class EmployeePreferencesModel(Base):
    """
    Employee preferences model representing an employee's shift preferences.
    
    Preferences can include preferred shift templates, specific days of the week,
    preferred time ranges, and importance weights. These are used as soft constraints
    in the optimization objective function to improve employee satisfaction.
    
    Attributes:
        preference_id: Primary key identifier
        user_id: Foreign key to the user (employee) who owns this preference
        preferred_shift_template_id: Optional FK to a preferred shift template
        preferred_day_of_week: Optional preferred day (enum: MONDAY-SUNDAY)
        preferred_start_time: Optional preferred start time (time only)
        preferred_end_time: Optional preferred end time (time only)
        preference_weight: Importance weight (0.0-1.0), higher = more important
        user: Relationship to the User who owns this preference
        shift_template: Relationship to the preferred ShiftTemplate (if specified)
    """
    __tablename__ = "employee_preferences"

    preference_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Preferred shift template (optional)
    preferred_shift_template_id = Column(
        Integer,
        ForeignKey("shift_templates.shift_template_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Preferred day of week (optional)
    preferred_day_of_week = Column(
        SqlEnum(DayOfWeek),
        nullable=True
    )
    
    # Preferred time range (optional)
    preferred_start_time = Column(Time, nullable=True)
    preferred_end_time = Column(Time, nullable=True)
    
    # Preference weight: 0.0 (least important) to 1.0 (most important)
    preference_weight = Column(Float, nullable=False, default=0.5)

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="preferences",
        lazy="selectin"
    )
    
    shift_template = relationship(
        "ShiftTemplateModel",
        lazy="selectin"
    )

    # Composite index for common queries
    __table_args__ = (
        Index('idx_user_preferences', 'user_id'),
    )
