from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.roleModel import RoleModel
from app.schemas.roleSchema import RoleCreate


async def create_role(db: Session, role_data: RoleCreate):
    try:
        existing = db.query(RoleModel).filter(
            RoleModel.role_name == role_data.role_name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Role '{role_data.role_name}' already exists.")

        new_role = RoleModel(**role_data.dict())
        db.add(new_role)
        db.commit()
        db.refresh(new_role)

        return new_role

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Database error: {str(e)}")


async def get_all_roles(db: Session):
    try:
        roles = db.query(RoleModel).all()
        return roles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


async def get_role(db: Session, role_id: int):
    try:
        role = db.query(RoleModel).filter(RoleModel.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Role not found")

        return role
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


async def delete_role(db: Session, role_id: int):
    try:
        role = db.query(RoleModel).filter(RoleModel.role_id == role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Role not found")

        db.delete(role)
        db.commit()

        return {
            "message": "Role deleted successfully"
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Database error: {str(e)}")
