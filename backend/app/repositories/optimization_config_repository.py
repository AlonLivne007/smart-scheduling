"""
Optimization config repository for database operations on optimization configs.

This repository handles all database access for OptimizationConfigModel.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.db.models.optimizationConfigModel import OptimizationConfigModel
from app.exceptions.repository import NotFoundError


class OptimizationConfigRepository(BaseRepository[OptimizationConfigModel]):
    """Repository for optimization config database operations."""
    
    def __init__(self, db: Session):
        """Initialize optimization config repository."""
        super().__init__(db, OptimizationConfigModel)
    
    def get_by_name(self, config_name: str) -> Optional[OptimizationConfigModel]:
        """Get a config by name."""
        return self.find_one_by(config_name=config_name)
    
    def get_default(self) -> Optional[OptimizationConfigModel]:
        """Get the default configuration."""
        return self.find_one_by(is_default=True)
    
    def get_default_or_raise(self) -> OptimizationConfigModel:
        """Get the default configuration, raising NotFoundError if not found."""
        config = self.get_default()
        if config is None:
            raise NotFoundError("No default optimization configuration found")
        return config
    
    def set_default(self, config_id: int) -> OptimizationConfigModel:
        """
        Set a configuration as default (unsetting others).
        
        Args:
            config_id: Config ID to set as default
            
        Returns:
            Updated config
        """
        # Unset all defaults
        self.db.query(OptimizationConfigModel).update({"is_default": False})
        
        # Set this one as default
        return self.update(config_id, is_default=True)
