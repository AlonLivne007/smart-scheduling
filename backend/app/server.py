"""
FastAPI application entry point.

This module initializes the FastAPI application, configures database tables,
and registers API route handlers for the Smart Scheduling system.
"""

from fastapi import FastAPI
from app.api.routes import usersRoutes, rolesRoutes
from app.db.session import engine, Base
from app.db.models import userModel, roleModel, userRoleModel

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(title="Smart Scheduling API")

# Register API routes
app.include_router(usersRoutes.router)
app.include_router(rolesRoutes.router)
