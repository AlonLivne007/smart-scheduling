"""
Shift template repository for database operations on shift templates.

This repository handles all database access for ShiftTemplateModel.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, delete, insert

from app.repositories.base import BaseRepository
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.roleModel import RoleModel
from app.exceptions.repository import NotFoundError


class ShiftTemplateRepository(BaseRepository[ShiftTemplateModel]):
    """Repository for shift template database operations."""
    
    def __init__(self, db: Session):
        """Initialize shift template repository."""
        super().__init__(db, ShiftTemplateModel)
    
    def get_by_name(self, template_name: str) -> Optional[ShiftTemplateModel]:
        """Get a template by name."""
        return self.find_one_by(shift_template_name=template_name)
    
    def get_with_roles(self, template_id: int) -> Optional[ShiftTemplateModel]:
        """Get a template with its required roles eagerly loaded."""
        return (
            self.db.query(ShiftTemplateModel)
            .options(joinedload(ShiftTemplateModel.required_roles))
            .filter(ShiftTemplateModel.shift_template_id == template_id)
            .first()
        )
    
    def assign_roles(self, template_id: int, role_ids: List[int]) -> ShiftTemplateModel:
        """
        Assign roles to a template (replaces existing roles).
        
        Args:
            template_id: Template ID
            role_ids: List of role IDs to assign
            
        Returns:
            Updated template with roles
            
        Raises:
            NotFoundError: If template or any role is not found
        """
        template = self.get_by_id_or_raise(template_id)
        
        # Fetch roles
        roles = self.db.query(RoleModel).filter(RoleModel.role_id.in_(role_ids)).all()
        found_ids = {r.role_id for r in roles}
        missing = [rid for rid in role_ids if rid not in found_ids]
        
        if missing:
            raise NotFoundError(f"The following role IDs do not exist: {missing}")
        
        # Replace roles
        template.required_roles = roles
        self.db.flush()
        return template
    
    def get_role_requirements_with_counts(
        self,
        template_ids: List[int]
    ) -> Dict[int, Dict[int, int]]:
        """
        Get role requirements with counts for multiple templates.
        
        Returns mapping: template_id -> {role_id: required_count}
        
        Args:
            template_ids: List of template IDs
            
        Returns:
            Dictionary mapping template_id to {role_id: required_count}
        """
        if not template_ids:
            return {}
        
        from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
        
        all_requirements = self.db.execute(
            select(
                shift_role_requirements.c.shift_template_id,
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count
            ).where(
                shift_role_requirements.c.shift_template_id.in_(template_ids)
            )
        ).all()
        
        template_role_map: Dict[int, Dict[int, int]] = {}
        for row in all_requirements:
            template_id = row.shift_template_id
            if template_id not in template_role_map:
                template_role_map[template_id] = {}
            template_role_map[template_id][row.role_id] = row.required_count
        
        return template_role_map
    
    def get_role_requirements_for_template(
        self,
        template_id: int
    ) -> List[Dict]:
        """
        Get role requirements with counts and names for a single template.
        
        Args:
            template_id: Template ID
            
        Returns:
            List of dicts with role_id, required_count, role_name
        """
        from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
        
        rows = self.db.execute(
            select(
                shift_role_requirements.c.role_id,
                shift_role_requirements.c.required_count,
                RoleModel.role_name,
            )
            .join(RoleModel, RoleModel.role_id == shift_role_requirements.c.role_id)
            .where(shift_role_requirements.c.shift_template_id == template_id)
        ).all()
        
        return [
            {
                'role_id': row.role_id,
                'required_count': row.required_count,
                'role_name': row.role_name,
            }
            for row in rows
        ]
    
    def set_role_requirements(
        self,
        template_id: int,
        role_requirements: List[Dict]
    ) -> None:
        """
        Set role requirements for a template (replaces existing).
        
        Args:
            template_id: Template ID
            role_requirements: List of dicts with 'role_id' and 'required_count'
        """
        from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
        
        # Delete existing requirements
        self.db.execute(
            delete(shift_role_requirements).where(
                shift_role_requirements.c.shift_template_id == template_id
            )
        )
        
        # Add new requirements
        if role_requirements:
            self.db.execute(
                insert(shift_role_requirements),
                [
                    {
                        "shift_template_id": template_id,
                        "role_id": req['role_id'],
                        "required_count": req.get('required_count', 1),
                    }
                    for req in role_requirements
                ],
            )
        
        self.db.flush()
