from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class WeeklyScheduleModel(Base):
    __tablename__ = "shift_weekly_schedule"
    weekly_schedule_id = Column(Integer, primary_key=True, index=True)
    week_start_date = Column(DateTime, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.user_id", nullable=False))
    created_by = relationship("UserModel", back_populates="weekly_schedules")

    planned_shifts = relationship(
        "PlannedShiftModel",
        back_populates="weekly_schedule",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WeeklySchedule(id={self.weekly_schedule_id}, week_start={self.week_start_date})>"
