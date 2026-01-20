"""
Role repository for database operations on roles.

This repository handles all database access for RoleModel.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import BaseRepository
from app.data.models.role_model import RoleModel
from app.exceptions.repository import NotFoundError


class RoleRepository(BaseRepository[RoleModel]):
    """Repository for role database operations."""
    
    def __init__(self, db: Session):
        """Initialize role repository."""
        super().__init__(db, RoleModel)
    
    def get_by_name(self, role_name: str) -> Optional[RoleModel]:
        """Get a role by name."""
        return self.find_one_by(role_name=role_name)
    
    def get_by_name_or_raise(self, role_name: str) -> RoleModel:
        """Get a role by name, raising NotFoundError if not found."""
        role = self.get_by_name(role_name)
        if role is None:
            raise NotFoundError(f"Role with name {role_name} not found")
        return role
    
    def get_with_users(self, role_id: int) -> Optional[RoleModel]:
        """Get a role with its users eagerly loaded."""
        return (
            self.db.query(RoleModel)
            .options(joinedload(RoleModel.users))
            .filter(RoleModel.role_id == role_id)
            .first()
        )
