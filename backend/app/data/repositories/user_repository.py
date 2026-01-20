"""
User repository for database operations on users.

This repository handles all database access for UserModel. It should be the
only place where UserModel is queried or modified directly.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.data.repositories.base import BaseRepository
from app.data.models.user_model import UserModel
from app.data.models.role_model import RoleModel
from app.core.exceptions.repository import NotFoundError


class UserRepository(BaseRepository[UserModel]):
    """
    Repository for user database operations.
    
    Provides methods for user CRUD operations and domain-specific queries.
    """
    
    def __init__(self, db: Session):
        """Initialize user repository."""
        super().__init__(db, UserModel)
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User if found, None otherwise
        """
        return self.find_one_by(user_email=email)
    
    def get_by_email_or_raise(self, email: str) -> UserModel:
        """
        Get a user by email, raising NotFoundError if not found.
        
        Args:
            email: User's email address
            
        Returns:
            User
            
        Raises:
            NotFoundError: If user is not found
        """
        user = self.get_by_email(email)
        if user is None:
            raise NotFoundError(f"User with email {email} not found")
        return user
    
    def get_with_roles(self, user_id: int) -> Optional[UserModel]:
        """
        Get a user with their roles eagerly loaded.
        
        Args:
            user_id: User's ID
            
        Returns:
            User with roles loaded, or None if not found
        """
        return (
            self.db.query(UserModel)
            .options(joinedload(UserModel.roles))
            .filter(UserModel.user_id == user_id)
            .first()
        )
    
    def get_all_with_roles(self) -> List[UserModel]:
        """
        Get all users with their roles eagerly loaded.
        
        Returns:
            List of users with roles loaded
        """
        return (
            self.db.query(UserModel)
            .options(joinedload(UserModel.roles))
            .all()
        )
    
    def get_managers(self) -> List[UserModel]:
        """
        Get all users who are managers.
        
        Returns:
            List of manager users
        """
        return self.find_by(is_manager=True)
    
    def get_active_users(self) -> List[UserModel]:
        """
        Get all users.
        
        Note: This method is kept for backward compatibility.
        Since user_status field was removed, it now returns all users.
        
        Returns:
            List of all users
        """
        return self.get_all()
    
    def assign_roles(self, user_id: int, role_ids: List[int]) -> UserModel:
        """
        Assign roles to a user (replaces existing roles).
        
        Args:
            user_id: User's ID
            role_ids: List of role IDs to assign
            
        Returns:
            Updated user with roles
            
        Raises:
            NotFoundError: If user or any role is not found
        """
        user = self.get_or_raise(user_id)
        
        # Fetch roles
        roles = self.db.query(RoleModel).filter(RoleModel.role_id.in_(role_ids)).all()
        found_ids = {r.role_id for r in roles}
        missing = [rid for rid in role_ids if rid not in found_ids]
        
        if missing:
            raise NotFoundError(f"The following role IDs do not exist: {missing}")
        
        # Replace roles
        user.roles = roles
        self.db.flush()
        return user
