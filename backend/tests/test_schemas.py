"""Test Pydantic schemas for optimization models."""

from app.schemas.optimizationConfigSchema import (
    OptimizationConfigCreate,
    OptimizationConfigUpdate,
    OptimizationConfigRead
)
from app.schemas.schedulingRunSchema import (
    SchedulingRunCreate,
    SchedulingRunRead,
    SchedulingRunSummary
)
from app.schemas.schedulingSolutionSchema import (
    SchedulingSolutionCreate,
    SchedulingSolutionRead,
    ApplySolutionRequest
)
from app.db.models.schedulingRunModel import SchedulingRunStatus, SolverStatus
from datetime import datetime

print('=== Testing OptimizationConfig Schemas ===')
config_create = OptimizationConfigCreate(
    config_name="Test Config",
    weight_fairness=0.25,
    weight_preferences=0.5,
    weight_cost=0.1,
    weight_coverage=0.15,
    max_runtime_seconds=180,
    mip_gap=0.02,
    is_default=False
)
print(f'✅ OptimizationConfigCreate: {config_create.config_name}')
print(f'   Weights sum: {config_create.weight_fairness + config_create.weight_preferences + config_create.weight_cost + config_create.weight_coverage}')

# Test update
config_update = OptimizationConfigUpdate(
    weight_fairness=0.35,
    max_runtime_seconds=600
)
print(f'✅ OptimizationConfigUpdate: Updated {len(config_update.model_dump(exclude_unset=True))} fields')

print('\n=== Testing SchedulingRun Schemas ===')
run_create = SchedulingRunCreate(
    weekly_schedule_id=1,
    config_id=1
)
print(f'✅ SchedulingRunCreate: Schedule={run_create.weekly_schedule_id}, Config={run_create.config_id}')

print('\n=== Testing SchedulingSolution Schemas ===')
solution_create = SchedulingSolutionCreate(
    run_id=1,
    planned_shift_id=10,
    user_id=5,
    role_id=2,
    is_selected=True,
    assignment_score=0.85
)
print(f'✅ SchedulingSolutionCreate: Run={solution_create.run_id}, Shift={solution_create.planned_shift_id}')
print(f'   Employee={solution_create.user_id}, Role={solution_create.role_id}, Score={solution_create.assignment_score}')

# Test apply solution request
apply_request = ApplySolutionRequest(
    overwrite_existing=False,
    only_selected=True
)
print(f'✅ ApplySolutionRequest: Overwrite={apply_request.overwrite_existing}, Only selected={apply_request.only_selected}')

print('\n=== Testing Enum Values ===')
print(f'SchedulingRunStatus values: {[s.value for s in SchedulingRunStatus]}')
print(f'SolverStatus values: {[s.value for s in SolverStatus]}')

print('\n✅ All schema tests passed!')
