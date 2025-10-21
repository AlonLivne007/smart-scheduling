"""
Pydantic schemas for the Role model.

These schemas define the structure of Role-related data used for API requests
and responses. They ensure proper validation of Role names and relationships
with Users.

"""
from typing import Optional

from pydantic import BaseModel


class RoleBase(BaseModel):
    """
    Base schema containing common fields shared by all Role operations.
    """
    role_name: str


class RoleCreate(RoleBase):
    """
    Schema used when creating a new Role.
    """
    role_name: str


class RoleUpdate(BaseModel):
    """
    Schema used when updating an existing Role.
    """
    role_name: Optional[str] = None


class RoleRead(RoleBase):
    """
    Schema returned when reading Role data from the database.
    Includes the unique identifier of the Role.
    """
    role_id: int

    model_config = {"from_attributes": True}
