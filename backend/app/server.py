"""
FastAPI application entry point.

This module initializes the FastAPI application, configures database tables,
and registers API route handlers for the Smart Scheduling system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import usersRoutes, rolesRoutes, shiftTemplateRoutes, weeklyScheduleRoutes, plannedShiftRoutes, shiftAssignmentRoutes
from app.db.session import engine, Base
from app.db.models import roleModel, userModel, userRoleModel,shiftTemplateModel, shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel # Ensure all models are imported for table creation

# Create database tables
Base.metadata.create_all(bind=engine)
print("📋 Tables registered in metadata:", Base.metadata.tables.keys())

# Initialize FastAPI application
app = FastAPI(title="Smart Scheduling API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://frontend:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(usersRoutes.router)
app.include_router(rolesRoutes.router)
app.include_router(shiftTemplateRoutes.router)

app.include_router(weeklyScheduleRoutes.router)

app.include_router(plannedShiftRoutes.router)

app.include_router(shiftAssignmentRoutes.router)
