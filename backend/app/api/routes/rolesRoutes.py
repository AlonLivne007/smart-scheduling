from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.controllers.roleController import create_role, get_all_roles
from app.schemas.roleSchema import RoleRead, RoleCreate

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.post("/", response_model=RoleRead, status_code=201)
def add_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    """
    Endpoint: Create a new role.
    """
    return create_role(db, role_data.role_name)

@router.get("/", response_model=List[RoleRead])
def list_roles(db: Session = Depends(get_db)):
    """
    Endpoint: Get all roles.
    """
    return get_all_roles(db)
