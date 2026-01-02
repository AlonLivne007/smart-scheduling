# backend/app/server.py
"""
FastAPI application entry point.

This module initializes the FastAPI application, configures database tables,
and registers API route handlers for the Smart Scheduling system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    usersRoutes,
    rolesRoutes,
    shiftTemplateRoutes,
    weeklyScheduleRoutes,
    plannedShiftRoutes,
    shiftAssignmentRoutes,
    timeOffRequestRoutes,
    systemConstraintsRoutes,
    employeePreferencesRoutes,
    optimizationConfigRoutes,
    schedulingRoutes,
    schedulingRunRoutes,
)
from app.db.session import engine, Base
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)
from app.db.initMasterUser import init_master_user
from app.db.seed_test_data import init_test_data

# Create database tables
Base.metadata.create_all(bind=engine)
print("📋 Tables registered in metadata:", Base.metadata.tables.keys())

# Initialize master user on startup
init_master_user()

# Seed test data on startup (idempotent; will skip if already present)
init_test_data()

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

app.include_router(timeOffRequestRoutes.router)

app.include_router(systemConstraintsRoutes.router)

app.include_router(employeePreferencesRoutes.router)

app.include_router(optimizationConfigRoutes.router)

app.include_router(schedulingRoutes.router)

app.include_router(schedulingRunRoutes.router)
