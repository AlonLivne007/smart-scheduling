from fastapi import FastAPI
from app.api.routes import usersRoutes, rolesRoutes


from app.db.session import engine, Base
from app.db.models import userModel, roleModel, userRoleModel

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smart Scheduling API")

app.include_router(usersRoutes.router)
app.include_router(rolesRoutes.router)
