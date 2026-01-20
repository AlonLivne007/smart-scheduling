"""
Optimization configuration schema definitions.

This module contains Pydantic schemas for OptimizationConfig API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class OptimizationConfigBase(BaseModel):
    """Base schema with common fields for optimization configuration."""
    
    config_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Descriptive name for the configuration"
    )
    
    weight_fairness: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for workload fairness (0.0-1.0)"
    )
    
    weight_preferences: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for employee preference satisfaction (0.0-1.0)"
    )
    
    weight_cost: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Weight for cost minimization (0.0-1.0)"
    )
    
    weight_coverage: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for shift coverage (0.0-1.0)"
    )
    
    max_runtime_seconds: int = Field(
        default=300,
        gt=0,
        le=3600,
        description="Maximum solver runtime in seconds (1-3600)"
    )
    
    mip_gap: float = Field(
        default=0.01,
        gt=0.0,
        le=1.0,
        description="MIP optimality gap tolerance (0.01 = 1%)"
    )
    
    is_default: bool = Field(
        default=False,
        description="Whether this is the default configuration"
    )

    @field_validator('weight_fairness', 'weight_preferences', 'weight_cost', 'weight_coverage')
    @classmethod
    def validate_weights(cls, v, info):
        """Ensure weight is between 0 and 1."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{info.field_name} must be between 0.0 and 1.0")
        return v


class OptimizationConfigCreate(OptimizationConfigBase):
    """
    Schema for creating a new optimization configuration.
    
    Example:
        {
            "config_name": "Balanced Schedule",
            "weight_fairness": 0.3,
            "weight_preferences": 0.4,
            "weight_cost": 0.1,
            "weight_coverage": 0.2,
            "max_runtime_seconds": 300,
            "mip_gap": 0.01,
            "is_default": false
        }
    """
    pass


class OptimizationConfigUpdate(BaseModel):
    """
    Schema for updating an optimization configuration.
    
    All fields are optional for partial updates.
    """
    
    config_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Descriptive name for the configuration"
    )
    
    weight_fairness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Weight for workload fairness (0.0-1.0)"
    )
    
    weight_preferences: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Weight for employee preference satisfaction (0.0-1.0)"
    )
    
    weight_cost: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Weight for cost minimization (0.0-1.0)"
    )
    
    weight_coverage: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Weight for shift coverage (0.0-1.0)"
    )
    
    max_runtime_seconds: Optional[int] = Field(
        None,
        gt=0,
        le=3600,
        description="Maximum solver runtime in seconds (1-3600)"
    )
    
    mip_gap: Optional[float] = Field(
        None,
        gt=0.0,
        le=1.0,
        description="MIP optimality gap tolerance (0.01 = 1%)"
    )
    
    is_default: Optional[bool] = Field(
        None,
        description="Whether this is the default configuration"
    )


class OptimizationConfigRead(OptimizationConfigBase):
    """
    Schema for reading optimization configuration data.
    
    Includes all fields plus metadata (id, timestamps).
    """
    
    config_id: int = Field(..., description="Configuration identifier")
    created_at: datetime = Field(..., description="When configuration was created")
    updated_at: datetime = Field(..., description="When configuration was last updated")

    class Config:
        from_attributes = True
