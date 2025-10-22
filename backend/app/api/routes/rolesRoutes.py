from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.controllers.roleController import (create_role, get_all_roles,
                                                get_role, delete_role)
from app.db.session import get_db
from app.schemas.roleSchema import RoleRead, RoleCreate

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", status_code=status.HTTP_201_CREATED,
             summary="Create a new role", )
async def add_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    return await create_role(db, role_data)


@router.get("/", response_model=List[RoleRead], status_code=status.HTTP_200_OK,
            summary="List all roles")
async def list_roles(db: Session = Depends(get_db)):
    return await get_all_roles(db)


@router.get("/{role_id}", response_model=RoleRead,
            status_code=status.HTTP_200_OK, summary="Get a single role by ID")
async def get_single_role(role_id: int, db: Session = Depends(get_db)):
    return await get_role(db, role_id)


@router.delete("/{role_id}", status_code=status.HTTP_200_OK,
               summary="Delete a role")
async def remove_role(role_id: int, db: Session = Depends(get_db)):
    return await delete_role(db, role_id)
