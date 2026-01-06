"""
Scheduling Service - Backward Compatibility Wrapper.

This module provides backward compatibility by re-exporting the refactored
scheduling service from the new modular package.
"""

# Import from the new modular package
from app.services.scheduling.scheduling_service import SchedulingService
from app.services.scheduling.types import SchedulingSolution

# Re-export for backward compatibility
__all__ = ['SchedulingService', 'SchedulingSolution']
