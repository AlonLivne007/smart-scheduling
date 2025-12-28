"""
Scheduling run model definition.

This module defines the SchedulingRun ORM model representing an optimization run
that tracks the execution of the MIP solver, its status, results, and metadata.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Enum as SqlEnum, \
    DateTime, Float, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class SchedulingRunStatus(enum.Enum):
    """
    Enumeration for scheduling run status states.
    
    Values:
        PENDING: Optimization queued but not started
        RUNNING: Optimization currently executing
        COMPLETED: Optimization finished successfully
        FAILED: Optimization failed due to error
        CANCELLED: Optimization cancelled by user
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SolverStatus(enum.Enum):
    """
    Enumeration for MIP solver status results.
    
    Values:
        OPTIMAL: Solver found the optimal solution
        FEASIBLE: Solver found a feasible solution (within time limit)
        INFEASIBLE: No feasible solution exists
        NO_SOLUTION_FOUND: Solver timeout, no solution found
        ERROR: Solver encountered an error
    """
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NO_SOLUTION_FOUND = "NO_SOLUTION_FOUND"
    ERROR = "ERROR"


class SchedulingRunModel(Base):
    """
    Scheduling run model representing an optimization execution instance.
    
    Tracks the entire lifecycle of an optimization run, from start to completion,
    including solver metrics, configuration used, and resulting solutions.
    
    Attributes:
        run_id: Primary key identifier
        weekly_schedule_id: Foreign key to the weekly schedule being optimized
        config_id: Foreign key to the optimization configuration used (nullable)
        status: Current status of the optimization run
        solver_status: Final status reported by the MIP solver (nullable)
        started_at: Timestamp when optimization started
        completed_at: Timestamp when optimization completed (nullable)
        runtime_seconds: Total runtime in seconds (nullable)
        objective_value: Final objective function value from solver (nullable)
        mip_gap: Final optimality gap achieved (nullable)
        total_assignments: Number of assignments in the solution (nullable)
        error_message: Error message if optimization failed (nullable)
        weekly_schedule: Relationship to the WeeklySchedule being optimized
        config: Relationship to the OptimizationConfig used
        solutions: Relationship to SchedulingSolution records (proposed assignments)
    """
    __tablename__ = "scheduling_runs"

    run_id = Column(Integer, primary_key=True, index=True)
    
    weekly_schedule_id = Column(
        Integer,
        ForeignKey("shift_weekly_schedule.weekly_schedule_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    config_id = Column(
        Integer,
        ForeignKey("optimization_configs.config_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Run status tracking
    status = Column(
        SqlEnum(SchedulingRunStatus, name="schedulingruns_status"),
        nullable=False,
        default=SchedulingRunStatus.PENDING,
        index=True
    )
    
    solver_status = Column(
        SqlEnum(SolverStatus, name="solver_status"),
        nullable=True
    )
    
    # Timing information
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    runtime_seconds = Column(Float, nullable=True)
    
    # Solver results
    objective_value = Column(Float, nullable=True)
    mip_gap = Column(Float, nullable=True)  # Final gap achieved
    total_assignments = Column(Integer, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    weekly_schedule = relationship(
        "WeeklyScheduleModel",
        back_populates="scheduling_runs",
        lazy="selectin"
    )
    
    config = relationship(
        "OptimizationConfigModel",
        lazy="selectin"
    )
    
    solutions = relationship(
        "SchedulingSolutionModel",
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index('idx_scheduling_run_schedule', 'weekly_schedule_id'),
        Index('idx_scheduling_run_status', 'status'),
        Index('idx_scheduling_run_started', 'started_at'),
    )

    def __repr__(self):
        """String representation of the scheduling run."""
        return (
            f"<SchedulingRun("
            f"id={self.run_id}, "
            f"schedule_id={self.weekly_schedule_id}, "
            f"status={self.status.value}, "
            f"solver_status={self.solver_status.value if self.solver_status else None})>"
        )
