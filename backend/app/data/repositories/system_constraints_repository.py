"""
System constraints repository for database operations on system constraints.

This repository handles all database access for SystemConstraintsModel.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.data.repositories.base import BaseRepository
from app.data.models.system_constraints_model import (
    SystemConstraintsModel,
    SystemConstraintType
)
from app.core.exceptions.repository import NotFoundError


class SystemConstraintsRepository(BaseRepository[SystemConstraintsModel]):
    """Repository for system constraints database operations."""
    
    def __init__(self, db: Session):
        """Initialize system constraints repository."""
        super().__init__(db, SystemConstraintsModel)
    
    def get_by_type(self, constraint_type: SystemConstraintType) -> Optional[SystemConstraintsModel]:
        """Get a constraint by type."""
        return self.find_one_by(constraint_type=constraint_type)
    
    def get_by_type_or_raise(self, constraint_type: SystemConstraintType) -> SystemConstraintsModel:
        """Get a constraint by type, raising NotFoundError if not found."""
        constraint = self.get_by_type(constraint_type)
        if constraint is None:
            raise NotFoundError(f"Constraint with type {constraint_type.value} not found")
        return constraint
    
    def get_hard_constraints(self) -> List[SystemConstraintsModel]:
        """Get all hard constraints."""
        return self.find_by(is_hard_constraint=True)
    
    def get_soft_constraints(self) -> List[SystemConstraintsModel]:
        """Get all soft constraints."""
        return self.find_by(is_hard_constraint=False)
