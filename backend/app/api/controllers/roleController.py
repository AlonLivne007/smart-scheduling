from sqlalchemy.orm import Session
from app.db.models.roleModel import Role
from fastapi import HTTPException

def create_role(db: Session, role_name: str):
    existing = db.query(Role).filter(Role.role_name.ilike(role_name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists.")
    new_role = Role(role_name=role_name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

def get_all_roles(db: Session):
    return db.query(Role).all()
