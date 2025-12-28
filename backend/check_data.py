"""Quick script to check existing data."""
import sys
sys.path.insert(0, '/app')

# Import all models first
from app.db.models import (
    roleModel, userModel, userRoleModel, shiftTemplateModel,
    shiftRoleRequirementsTabel, weeklyScheduleModel, plannedShiftModel, shiftAssignmentModel,
    timeOffRequestModel, systemConstraintsModel, employeePreferencesModel,
    optimizationConfigModel, schedulingRunModel, schedulingSolutionModel
)

from app.db.session import SessionLocal
from app.db.models.shiftTemplateModel import ShiftTemplateModel
from app.db.models.roleModel import RoleModel
from app.db.models.shiftRoleRequirementsTabel import shift_role_requirements
from sqlalchemy import select

db = SessionLocal()

print("=== SHIFT TEMPLATES ===")
templates = db.query(ShiftTemplateModel).all()
for t in templates:
    print(f"  - {t.shift_template_name}")

print("\n=== ROLES ===")
roles = db.query(RoleModel).all()
for r in roles:
    print(f"  - {r.role_name}")

print("\n=== SHIFT TEMPLATE ROLE REQUIREMENTS ===")
results = db.execute(select(shift_role_requirements)).all()
print(f"Total: {len(results)}")
for r in results[:10]:
    print(f"  Template {r[0]}: Role {r[1]} (count: {r[2]})")

db.close()
