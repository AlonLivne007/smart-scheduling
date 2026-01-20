"""
Base repository providing generic CRUD operations.

This module defines the BaseRepository class that provides common database
operations for all repositories. Entity-specific repositories should inherit
from this class and add domain-specific methods.
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.exceptions.repository import (
    RepositoryError,
    NotFoundError,
    ConflictError,
    DatabaseError,
)

# Type variable for the model class
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing generic CRUD operations.
    
    This class should be inherited by entity-specific repositories.
    It provides common operations like create, read, update, delete.
    
    Example:
        class UserRepository(BaseRepository[UserModel]):
            def __init__(self, db: Session):
                super().__init__(db, UserModel)
    """
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy database session (must be provided by caller)
            model: SQLAlchemy model class for this repository
        """
        self.db = db
        self.model = model
    
    def create(self, **kwargs) -> ModelType:
        """
        Create a new entity.
        
        Args:
            **kwargs: Attributes for the new entity
            
        Returns:
            The created entity instance
            
        Raises:
            ConflictError: If a unique constraint is violated
            DatabaseError: If a database error occurs
        """
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            self.db.flush()  # Flush to get ID, but don't commit yet
            return instance
        except IntegrityError as e:
            self.db.rollback()
            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
            raise ConflictError(f"Database constraint violation: {error_str}") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error during create: {str(e)}") from e
    
    def get_by_id(self, entity_id: int) -> Optional[ModelType]:
        """
        Get an entity by its primary key.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            The entity if found, None otherwise
        """
        try:
            return self.db.get(self.model, entity_id)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during get_by_id: {str(e)}") from e
    
    def get_by_id_or_raise(self, entity_id: int) -> ModelType:
        """
        Get an entity by its primary key, raising NotFoundError if not found.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            The entity
            
        Raises:
            NotFoundError: If the entity is not found
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(f"{self.model.__name__} with id {entity_id} not found")
        return entity
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[ModelType]:
        """
        Get all entities, optionally paginated.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of entities
        """
        try:
            query = self.db.query(self.model)
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during get_all: {str(e)}") from e
    
    def find_by(self, **filters) -> List[ModelType]:
        """
        Find entities matching the given filters.
        
        Args:
            **filters: Attribute-value pairs to filter by
            
        Returns:
            List of matching entities
            
        Example:
            users = user_repo.find_by(is_manager=True, user_status="ACTIVE")
        """
        try:
            query = self.db.query(self.model)
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == value)
            return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during find_by: {str(e)}") from e
    
    def find_one_by(self, **filters) -> Optional[ModelType]:
        """
        Find a single entity matching the given filters.
        
        Args:
            **filters: Attribute-value pairs to filter by
            
        Returns:
            The first matching entity, or None if not found
        """
        try:
            query = self.db.query(self.model)
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == value)
            return query.first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during find_one_by: {str(e)}") from e
    
    def update(self, entity_id: int, **kwargs) -> ModelType:
        """
        Update an entity by ID.
        
        Args:
            entity_id: Primary key value
            **kwargs: Attributes to update
            
        Returns:
            The updated entity
            
        Raises:
            NotFoundError: If the entity is not found
            ConflictError: If a unique constraint is violated
            DatabaseError: If a database error occurs
        """
        try:
            entity = self.get_by_id_or_raise(entity_id)
            
            for attr, value in kwargs.items():
                if hasattr(entity, attr) and value is not None:
                    setattr(entity, attr, value)
            
            self.db.flush()  # Flush but don't commit yet
            return entity
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.db.rollback()
            error_str = str(e.orig) if hasattr(e, 'orig') else str(e)
            raise ConflictError(f"Database constraint violation: {error_str}") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error during update: {str(e)}") from e
    
    def delete(self, entity_id: int) -> None:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: Primary key value
            
        Raises:
            NotFoundError: If the entity is not found
            DatabaseError: If a database error occurs
        """
        try:
            entity = self.get_by_id_or_raise(entity_id)
            self.db.delete(entity)
            self.db.flush()  # Flush but don't commit yet
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Database error during delete: {str(e)}") from e
    
    def exists(self, entity_id: int) -> bool:
        """
        Check if an entity exists by ID.
        
        Args:
            entity_id: Primary key value
            
        Returns:
            True if the entity exists, False otherwise
        """
        return self.get_by_id(entity_id) is not None
    
    def count(self, **filters) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            **filters: Attribute-value pairs to filter by
            
        Returns:
            Number of matching entities
        """
        try:
            query = self.db.query(self.model)
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    query = query.filter(getattr(self.model, attr) == value)
            return query.count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during count: {str(e)}") from e
