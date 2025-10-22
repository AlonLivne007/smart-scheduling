from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.session import Base


class UserRoleModel(Base):
    """
    Association table for the many-to-many relationship between users and roles.
    """
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
