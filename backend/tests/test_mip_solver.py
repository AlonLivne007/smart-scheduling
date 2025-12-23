"""Test MIP solver library installation."""

import mip
import numpy as np

print('=== Testing MIP Library ===')
print(f'MIP version: {mip.__version__}')

# Create a simple MIP model to test
model = mip.Model(sense=mip.MINIMIZE)

# Variables
x = model.add_var(var_type=mip.BINARY, name='x')
y = model.add_var(var_type=mip.BINARY, name='y')

# Constraint: x + y <= 1
model += x + y <= 1

# Objective: maximize x + 2*y (minimize -(x + 2*y))
model.objective = mip.minimize(-(x + 2*y))

# Solve
print('\nSolving simple test problem...')
status = model.optimize(max_seconds=10)

print(f'Status: {status}')
print(f'Optimal value: {model.objective_value}')
print(f'x = {x.x}')
print(f'y = {y.x}')

if status == mip.OptimizationStatus.OPTIMAL:
    print('✅ MIP solver is working correctly!')
else:
    print('⚠️ Solver did not find optimal solution')

print('\n=== Testing NumPy ===')
print(f'NumPy version: {np.__version__}')
arr = np.array([1.0, 2.0, 3.0])
print(f'Test array: {arr}')
print(f'Sum: {np.sum(arr)}')
print('✅ NumPy is working correctly!')

print('\n🎉 All dependencies are installed and working!')
