"""Test script to verify optimization tables were created correctly."""

from sqlalchemy import inspect
from app.db.session import engine

inspector = inspect(engine)

# Check optimization_configs table
print('=== optimization_configs ===')
for col in inspector.get_columns('optimization_configs'):
    print(f'  {col["name"]}: {col["type"]}')

print('\n=== scheduling_runs ===')
for col in inspector.get_columns('scheduling_runs'):
    print(f'  {col["name"]}: {col["type"]}')

print('\n=== scheduling_solutions ===')
for col in inspector.get_columns('scheduling_solutions'):
    print(f'  {col["name"]}: {col["type"]}')

# Check foreign keys
print('\n=== Foreign Keys in scheduling_runs ===')
fks = inspector.get_foreign_keys('scheduling_runs')
for fk in fks:
    print(f'  {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')

print('\n=== Foreign Keys in scheduling_solutions ===')
fks = inspector.get_foreign_keys('scheduling_solutions')
for fk in fks:
    print(f'  {fk["constrained_columns"]} -> {fk["referred_table"]}.{fk["referred_columns"]}')

print('\n✅ All optimization tables verified!')
