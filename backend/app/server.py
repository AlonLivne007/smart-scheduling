# backend/app/server.py
"""
FastAPI application entry point.

This module initializes the FastAPI application, configures database tables,
and registers API route handlers for the Smart Scheduling system.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Import exception handlers
from app.api.middleware.error_handlers import (
    not_found_error_handler,
    conflict_error_handler,
    database_error_handler,
    validation_error_handler,
    business_rule_error_handler,
    repository_error_handler,
    service_error_handler,
)
from app.core.exceptions.repository import (
    NotFoundError,
    ConflictError,
    DatabaseError,
    RepositoryError,
)
from app.core.exceptions.service import (
    ValidationError,
    BusinessRuleError,
    ServiceError,
)

from app.api.routes import (
    users_routes,
    roles_routes,
    shift_template_routes,
    weekly_schedule_routes,
    planned_shift_routes,
    shift_assignment_routes,
    time_off_request_routes,
    system_constraints_routes,
    employee_preferences_routes,
    optimization_config_routes,
    scheduling_routes,
    scheduling_run_routes,
    schedule_publishing_routes,
    activity_log_routes,
    metrics_routes,
    export_routes,
)
from app.data.session import engine, Base
from app.data.models import (
    role_model, user_model, user_role_model, shift_template_model,
    shift_role_requirements_table, weekly_schedule_model, planned_shift_model, shift_assignment_model,
    time_off_request_model, system_constraints_model, employee_preferences_model,
    optimization_config_model, scheduling_run_model, scheduling_solution_model, activity_log_model
)


# Create database tables
Base.metadata.create_all(bind=engine)
logger.debug(
    "Tables registered in metadata",
    extra={"tables": list(Base.metadata.tables.keys())}
)


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

# Register exception handlers
# Order matters: specific handlers should be registered before general ones
app.add_exception_handler(NotFoundError, not_found_error_handler)
app.add_exception_handler(ConflictError, conflict_error_handler)
app.add_exception_handler(DatabaseError, database_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(BusinessRuleError, business_rule_error_handler)
app.add_exception_handler(RepositoryError, repository_error_handler)
app.add_exception_handler(ServiceError, service_error_handler)

# Register API routes
app.include_router(users_routes.router)
app.include_router(roles_routes.router)
app.include_router(shift_template_routes.router)

app.include_router(weekly_schedule_routes.router)

app.include_router(planned_shift_routes.router)

app.include_router(shift_assignment_routes.router)

app.include_router(time_off_request_routes.router)

app.include_router(system_constraints_routes.router)

app.include_router(employee_preferences_routes.router)

app.include_router(optimization_config_routes.router)

app.include_router(scheduling_routes.router)

app.include_router(scheduling_run_routes.router)

app.include_router(schedule_publishing_routes.router)

app.include_router(activity_log_routes.router)

app.include_router(metrics_routes.router)

app.include_router(export_routes.router)
