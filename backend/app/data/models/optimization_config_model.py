"""
Optimization configuration model definition.

This module defines the OptimizationConfig ORM model representing configuration
settings for the MIP optimizer, including objective function weights and solver parameters.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.data.session import Base


class OptimizationConfigModel(Base):
    """
    Optimization configuration model representing solver parameters and objective weights.
    
    Managers can create multiple configurations to experiment with different optimization
    objectives (e.g., prioritize fairness vs preferences vs coverage).
    
    Attributes:
        config_id: Primary key identifier
        config_name: Descriptive name for the configuration (unique)
        weight_fairness: Weight for workload fairness in objective function (0.0-1.0)
        weight_preferences: Weight for employee preference satisfaction (0.0-1.0)
        weight_cost: Weight for cost minimization (future use) (0.0-1.0)
        weight_coverage: Weight for shift coverage (0.0-1.0)
        max_runtime_seconds: Maximum solver runtime in seconds (timeout)
        mip_gap: Optimality gap tolerance (0.01 = 1%, solver stops when within gap)
        is_default: Whether this is the default configuration
        created_at: Timestamp when configuration was created
        updated_at: Timestamp when configuration was last updated
    """
    __tablename__ = "optimization_configs"

    config_id = Column(Integer, primary_key=True, index=True)
    
    config_name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Objective function weights (0.0 to 1.0)
    # These determine what the optimizer prioritizes
    weight_fairness = Column(Float, nullable=False, default=0.3)
    weight_preferences = Column(Float, nullable=False, default=0.4)
    weight_cost = Column(Float, nullable=False, default=0.1)
    weight_coverage = Column(Float, nullable=False, default=0.2)
    
    # Solver parameters
    max_runtime_seconds = Column(
        Integer,
        nullable=False,
        default=300  # 5 minutes default
    )
    
    mip_gap = Column(
        Float,
        nullable=False,
        default=0.01  # 1% optimality gap
    )
    
    # Flag to mark the default configuration
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_optimization_config_name', 'config_name'),
        Index('idx_optimization_config_default', 'is_default'),
    )

    def __repr__(self):
        """String representation of the optimization configuration."""
        return (
            f"<OptimizationConfig("
            f"id={self.config_id}, "
            f"name='{self.config_name}', "
            f"fairness={self.weight_fairness}, "
            f"preferences={self.weight_preferences}, "
            f"default={self.is_default})>"
        )
