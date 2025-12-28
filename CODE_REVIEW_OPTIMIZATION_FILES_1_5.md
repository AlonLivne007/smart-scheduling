# Code Review – Optimization System (Files 1–5)

## Executive Summary

This review covers 5 core files of the shift-scheduling optimization system. The following are the highest-impact issues requiring immediate attention:

1. **🔴 CRITICAL: Role coverage model is fundamentally incorrect** (schedulingService.py)

   - MIP uses `x[i,j]` (employee × shift) but constraints require per-role coverage
   - Same variable counted for multiple roles, leading to incorrect coverage
   - Post-solve role assignment is arbitrary and can violate requirements

2. **🔴 CRITICAL: Overnight shift handling is broken across multiple modules**

   - `_shifts_overlap()` in precompute ignores date field and doesn't normalize overnight shifts
   - Duration calculations produce negative values for overnight shifts
   - Validator's `_times_overlap()` only compares time-of-day, missing cross-day overlaps
   - Preference time overlap calculation doesn't handle overnight ranges

3. **🔴 CRITICAL: Coverage constraints allow infeasible solutions** (schedulingService.py)

   - When no eligible employees exist for a role, constraint is skipped
   - Model can produce "solutions" that ignore required coverage

4. **🟠 MAJOR: Contract mismatch in role requirements schema**

   - `OptimizationData.role_requirements` stores only `List[int]` (role IDs)
   - Shifts contain `required_roles` with `{'role_id', 'required_count'}`
   - Builder drops `required_count` when building `role_requirements`
   - Solver expects `required_count` but uses wrong data structure

5. **🟠 MAJOR: Availability matrix doesn't match its own docstring** (optimization_data_builder.py)

   - Claims to check overlap with existing assignments, but no such logic exists
   - Only checks time-off and direct assignment conflicts

6. **🟠 MAJOR: N+1 query problem in weekly schedule validation** (constraintService.py)

   - `validate_weekly_schedule()` calls `validate_assignment()` repeatedly
   - Each call queries DB for user, shift, time-off, roles separately
   - Should batch-load all context upfront

7. **🟠 MAJOR: Rest hours calculation is incorrect** (constraintService.py)

   - `_calculate_hours_between_shifts()` uses absolute difference
   - Should compute `(later.start - earlier.end)` and handle negative as overlap
   - Current logic can report incorrect rest periods

8. **🟠 MAJOR: Fairness variable indexing mismatch** (schedulingService.py)

   - `assignments_per_employee` only includes employees with variables
   - But fairness deviation uses `enumerate(assignments_per_employee)` treating index as employee index
   - Should build `emp_total` for all employees in range(n_employees)

9. **🟢 MINOR: Data duplication in OptimizationData**

   - `employee_roles` dictionary duplicates `employees[*]['roles']`
   - Propose single source of truth

10. **🟢 MINOR: NumPy arrays initialized as None without validation**
    - `availability_matrix` and `preference_scores` can be None
    - No validation in `__init__` or before use
    - Should add invariants or validation methods

---

## Cross-cutting Issues (System-wide)

### Contract Mismatches Between Modules

#### 1. Role Requirements Schema Inconsistency

**Problem:** Three different representations of role requirements exist:

- **Shifts (DB/builder):** `shift['required_roles'] = [{'role_id': int, 'required_count': int}, ...]`
- **OptimizationData.role_requirements:** `Dict[int, List[int]]` (shift_id → role_ids only, **drops required_count**)
- **Solver expectations:** Uses `shift['required_roles']` directly with `required_count`

**Risk:** The builder's `build_role_requirements()` method (line 259-277) extracts only role IDs, discarding counts. The solver then correctly uses `shift['required_roles']` from the shift dictionaries, but `data.role_requirements` is misleading and unused. This creates confusion and potential bugs if future code relies on `data.role_requirements`.

**Impact:** Medium (currently works because solver uses shift dicts, but schema is inconsistent)

#### 2. Overnight Shift Handling Inconsistency

**Problem:** Multiple modules handle overnight shifts differently (or not at all):

- **precompute.\_shifts_overlap():** Claims to handle overnight but only compares `start_time < end_time` without date normalization
- **precompute.build_shift_durations():** Direct subtraction can produce negative durations
- **builder.\_calculate_time_overlap():** Only compares time-of-day, doesn't handle overnight (end < start)
- **constraintService.\_times_overlap():** Only compares time-of-day, ignores date
- **constraintService.\_check_shift_overlaps():** Filters by same date, missing cross-day overlaps

**Risk:** Overnight shifts (e.g., 22:00–06:00) are incorrectly handled:

- Overlap detection misses overlaps across midnight
- Duration calculations are negative
- Rest period calculations are wrong
- Preference matching fails for overnight preferences

**Impact:** High (affects correctness for night shifts)

#### 3. Shift Overlap Data Structure Mismatch

**Problem:**

- **precompute.build_shift_overlaps():** Returns `Dict[int, Set[int]]`
- **builder.detect_shift_overlaps():** Converts to `Dict[int, List[int]]` for "backward compatibility"
- **OptimizationData.shift_overlaps:** Documented as `Dict[int, List[int]]`

**Risk:** Minor (just a conversion, but unnecessary if we standardize on sets)

#### 4. Employee Roles Duplication

**Problem:**

- `employees[i]['roles']` contains role list
- `employee_roles[user_id]` duplicates the same data
- Both are used in different places

**Risk:** Low (data consistency risk if one is updated but not the other)

---

## File 1 – optimization_data.py (OptimizationData DTO)

### ✅ What's good

- Clear separation of concerns (DTO only, no business logic)
- Well-documented attributes
- Type hints present for most fields

### 🔴 Correctness issues

1. **NumPy arrays initialized as None without validation**

   - `availability_matrix` and `preference_scores` are `np.ndarray = None`
   - No validation that they're set before use
   - If builder fails partially, arrays remain None → runtime errors

2. **role_requirements format doesn't match actual usage**
   - Stores `Dict[int, List[int]]` (shift_id → role_ids)
   - But shifts contain `required_roles` with `{'role_id', 'required_count'}`
   - Builder drops `required_count` (see File 3)
   - Solver uses `shift['required_roles']` directly, not `data.role_requirements`
   - This field is misleading and potentially unused

### 🟠 Efficiency issues

- None identified (this is a DTO)

### 🟢 Readability / Modularity suggestions

1. **Add validation method**

   ```python
   def validate(self) -> List[str]:
       """Validate that all required fields are set. Returns list of errors."""
       errors = []
       if self.availability_matrix is None:
           errors.append("availability_matrix not set")
       if self.preference_scores is None:
           errors.append("preference_scores not set")
       # ... check other required fields
       return errors
   ```

2. **Consider using dataclass or Pydantic**
   - Would provide automatic validation and better type safety
   - Current manual `__init__` is fine but less maintainable

### Proposed changes (bulleted)

- Add `validate()` method to check all required fields are set
- Document that `role_requirements` may be unused (solver uses shift dicts directly)
- Consider making arrays non-optional with default empty arrays, or add validation
- Add invariant: `len(availability_matrix) == len(employees) × len(shifts)` if set

### Suggested invariants (type/shape contracts)

- If `availability_matrix` is set: `shape == (len(employees), len(shifts))` and `dtype == int`
- If `preference_scores` is set: `shape == (len(employees), len(shifts))` and `dtype == float`
- `employee_index` keys must match all `employees[*]['user_id']`
- `shift_index` keys must match all `shifts[*]['planned_shift_id']`
- `employee_roles[user_id]` must equal `employees[i]['roles']` where `employees[i]['user_id'] == user_id`

---

## File 2 – optimization_precompute.py

### 🔴 Correctness issues (be explicit)

1. **`_shifts_overlap()` docstring claims overnight handling, but implementation is wrong**

   - **Line 27-33:** Extracts `start_time` and `end_time` directly from shift dicts
   - **Problem:** If shifts have `date` field and `start_time`/`end_time` are datetime objects, the comparison works. But if they're time objects, it ignores the date.
   - **Problem:** Docstring says "end_time < start_time means end is next day" but code doesn't normalize this
   - **Current logic:** `start1_dt < end2_dt and start2_dt < end1_dt` - this works for datetime objects but fails if times are not normalized for overnight
   - **Missing:** No normalization when `end_time < start_time` to add 1 day to end_time

2. **`build_shift_durations()` may produce negative durations for overnight shifts**

   - **Line 91:** `duration_delta = end_time - start_time`
   - If `end_time` and `start_time` are datetime objects and the shift is overnight, this works correctly (end_time is next day).
   - **BUT:** If they're time objects or not properly normalized, `end_time < start_time` produces negative duration
   - **Risk:** Negative durations break max-hours constraints and fairness calculations

3. **`build_time_off_conflicts()` output is unordered/non-deterministic**

   - **Line 146:** `conflicts[emp_id] = list(conflicting_shifts_set)`
   - Converting set to list produces non-deterministic order
   - **Impact:** Low (order doesn't matter for correctness, but makes testing harder and logs inconsistent)

4. **Timezone/date assumptions not documented**
   - All date/time operations assume naive datetime objects
   - No handling of timezone-aware datetimes
   - No validation that dates are consistent

### 🟠 Efficiency issues

1. **`build_shift_overlaps()` is O(S²)**
   - **Line 52-65:** Nested loop over all shift pairs
   - For S shifts, performs S(S-1)/2 overlap checks
   - **Suggestion:** For large S, use sweep-line algorithm:
     - Sort shifts by start time
     - Use a data structure (e.g., sorted list) to track active shifts
     - Only check overlaps with currently active shifts
   - **Complexity:** O(S log S) instead of O(S²)

### 🟢 Readability / Modularity suggestions

1. **Extract time normalization into reusable function**

   - Create `normalize_shift_datetimes(shift) -> (start_dt, end_dt)` that:
     - Handles both datetime and time objects
     - Normalizes overnight shifts (if end < start, add 1 day to end)
     - Returns consistent datetime objects
   - Use this in `_shifts_overlap()` and `build_shift_durations()`

2. **Add type hints for shift dictionaries**
   - Currently `Dict` type is too generic
   - Consider `TypedDict` or at least document expected keys

### Proposed fix snippets (short)

```python
def normalize_shift_datetimes(shift: Dict) -> Tuple[datetime, datetime]:
    """
    Normalize shift start/end times to datetime objects, handling overnight shifts.

    If end_time < start_time (time-only), assumes end is next day.
    If both are datetime objects, returns as-is.
    """
    start = shift["start_time"]
    end = shift["end_time"]
    shift_date = shift.get("date")

    # Convert to datetime if needed
    if isinstance(start, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        start_dt = datetime.combine(shift_date, start)
    else:
        start_dt = start

    if isinstance(end, time):
        if shift_date is None:
            raise ValueError("Cannot normalize time without date")
        end_dt = datetime.combine(shift_date, end)
        # Handle overnight: if end < start, end is next day
        if end < start:
            end_dt += timedelta(days=1)
    else:
        end_dt = end
        # If both are datetime and end < start on same date, assume overnight
        if end_dt.date() == start_dt.date() and end_dt < start_dt:
            end_dt += timedelta(days=1)

    return start_dt, end_dt

def _shifts_overlap(shift1: Dict, shift2: Dict) -> bool:
    """Check if two shifts overlap in time."""
    start1_dt, end1_dt = normalize_shift_datetimes(shift1)
    start2_dt, end2_dt = normalize_shift_datetimes(shift2)

    return start1_dt < end2_dt and start2_dt < end1_dt

def build_shift_durations(shifts: List[Dict]) -> Dict[int, float]:
    """Build shift durations mapping: {shift_id: duration_hours}."""
    durations = {}
    for shift in shifts:
        shift_id = shift["planned_shift_id"]
        start_dt, end_dt = normalize_shift_datetimes(shift)
        duration_delta = end_dt - start_dt
        duration_hours = duration_delta.total_seconds() / 3600.0
        durations[shift_id] = duration_hours
    return durations
```

---

## File 3 – optimization_data_builder.py

### 🔴 Correctness issues

1. **`availability_matrix` does NOT match its own docstring**

   - **Docstring (lines 408-412):** Claims to check "The shift doesn't overlap with another shift they're already assigned to"
   - **Implementation (lines 396-476):** Only checks:
     1. Time-off conflicts (lines 432-446)
     2. Direct assignment conflicts (lines 448-458)
     3. Role qualification (lines 460-474)
   - **Missing:** No overlap check with existing assignments
   - **Impact:** Employee can be marked available for overlapping shifts if they have existing assignments

2. **`build_role_requirements()` drops `required_count`**

   - **Line 273-275:** Extracts only `req['role_id']`, discarding `required_count`
   - **Meanwhile:** Shifts contain full `required_roles` with counts (line 193-196)
   - **Solver uses:** `shift['required_roles']` directly (correct), but `data.role_requirements` is misleading
   - **Risk:** If future code relies on `data.role_requirements`, it won't have counts

3. **`detect_shift_overlaps()` depends on precompute overlap logic (currently wrong for overnight)**

   - **Line 592:** Calls `build_shift_overlaps(shifts)` from precompute
   - Inherits the overnight shift bug from File 2
   - **Impact:** Overlap detection fails for overnight shifts

4. **`build_preference_scores()` time overlap doesn't handle overnight**

   - **Line 612-647:** `_calculate_time_overlap()` converts times to minutes since midnight
   - **Problem:** If `pref_end < pref_start` or `shift_end < shift_start` (overnight), calculation is wrong
   - **Example:** Preference 22:00–06:00 vs shift 23:00–07:00 should overlap, but current logic fails
   - **Line 642:** `shift_duration = shift_end_min - shift_start_min` can be negative

5. **DB consistency: user_status checked as strings instead of enum**

   - **Line 137:** `UserModel.user_status.in_(["ACTIVE", "active"])`
   - **Line 218 (constraintService):** `user.user_status not in ["ACTIVE", "active"]`
   - **Problem:** Fragile string matching instead of enum
   - **Risk:** If enum values change or case differs, checks fail silently

6. **Day-of-week comparison may be inconsistent**
   - **Line 532:** `shift_day_of_week = self._date_to_day_of_week(shift_date)` returns string like "MONDAY"
   - **Line 547:** Compares with `pref.preferred_day_of_week.value` (assumes enum with `.value`)
   - **Risk:** If enum format differs, comparison fails

### 🟠 Efficiency issues

1. **Time-off marking is triple nested (emp × shift × timeoff periods)**

   - **Lines 433-446:** For each employee, for each shift, iterate time-off periods
   - **Better:** Use precomputed `time_off_conflicts` from precompute module (already computed at line 123)
   - **Current:** O(E × S × T) where T = time-off periods per employee
   - **Optimized:** O(E × S) by using precomputed conflicts

2. **Role checks recompute required role ids for each employee/shift**

   - **Lines 460-474:** For each employee, for each shift, extract `required_role_ids`
   - **Better:** Precompute `required_role_ids_per_shift = {shift_id: set(role_ids)}` once
   - **Current:** O(E × S × R) where R = roles per shift
   - **Optimized:** O(E × S) with precomputation

3. **Preferences query loads all preferences globally**
   - **Line 511:** `all_preferences = self.db.query(EmployeePreferencesModel).all()`
   - **Better:** Filter to only employees in `data.employees`
   - **Current:** Loads preferences for all employees in system
   - **Optimized:** Load only for relevant employees

### 🟢 Readability / Modularity

1. **Put all "time normalization" into precompute, reused by builder + validator**

   - Currently `_calculate_time_overlap()` duplicates logic that should be in precompute
   - Move to precompute module for reuse

2. **Separate "DB extraction" from "pure transformations"**

   - Methods like `build_availability_matrix()` mix DB access (none currently) with pure logic
   - Good separation already, but could be clearer

3. **Extract role requirement extraction to helper**
   - `required_role_ids = [req['role_id'] for req in shift['required_roles']]` appears multiple times
   - Create `_extract_required_role_ids(shift) -> Set[int]` helper

### Proposed changes

- Fix availability matrix to actually check overlaps with existing assignments (or update docstring)
- Remove `build_role_requirements()` or make it store full requirements with counts
- Use precomputed `time_off_conflicts` in availability matrix instead of recomputing
- Precompute `required_role_ids_per_shift` once
- Filter preferences query to relevant employees
- Fix `_calculate_time_overlap()` to handle overnight ranges
- Use enum for user_status checks instead of strings

---

## File 4 – constraintService.py

### 🔴 Correctness issues

1. **`_times_overlap()` compares only time-of-day and ignores date**

   - **Line 540-550:** Converts datetime to time, then compares `start1 < end2 and start2 < end1`
   - **Problem:** For shifts on different dates, this is incorrect
   - **Example:** Shift 1: 2024-01-01 22:00–06:00 (overnight), Shift 2: 2024-01-02 05:00–13:00
   - **Current logic:** Compares 22:00 < 13:00 and 05:00 < 06:00 → False (incorrect, they overlap)
   - **Fix:** Must use full datetime comparison, not just time-of-day

2. **`_check_shift_overlaps()` filters only same-date shifts**

   - **Line 298:** `PlannedShiftModel.date == shift.date`
   - **Problem:** Overnight shifts can overlap with next day's shifts
   - **Example:** Shift ending 2024-01-02 06:00 overlaps with shift starting 2024-01-02 05:00
   - **Current logic:** If shifts are on different dates, overlap check is skipped
   - **Fix:** Remove date filter or use datetime range overlap

3. **`_calculate_shift_hours()` can produce negative durations if end < start (overnight)**

   - **Line 570-579:** Direct subtraction without overnight normalization
   - **Problem:** If `shift.end_time` is time object and `end_time < start_time`, duration is negative
   - **Fix:** Normalize to datetime and handle overnight (add 1 day if end < start on same date)

4. **`_calculate_hours_between_shifts()` uses absolute difference incorrectly**

   - **Line 552-568:** Calculates `diff = start2 - end1` or `diff = end1 - start2` based on order
   - **Problem:** Uses absolute difference, but rest should be `(later.start - earlier.end)`
   - **If negative:** Indicates overlap, not rest period
   - **Current logic:** `if end1 < start2: diff = start2 - end1` is correct, but `else: diff = end1 - start2` is wrong
   - **Fix:** Always compute as `(later.start - earlier.end)`, return negative if overlap

5. **`validate_weekly_schedule()` runs N+1 queries via `validate_assignment()` repeatedly**
   - **Line 192-200:** Calls `validate_assignment()` for each assignment
   - **Each call queries:** User (line 133), Shift (line 134), Time-off (line 233), Roles (line 265)
   - **For N assignments:** ~4N queries instead of batched queries
   - **Fix:** Preload all users, shifts, time-off, roles in batches upfront

### 🟠 Efficiency issues

1. **Many DB calls inside loops**
   - **Lines 133-136:** Query user and shift for each assignment
   - **Line 233-238:** Query time-off for each assignment
   - **Line 265:** Query role for each assignment (if not found in user.roles)
   - **Line 296-299:** Query overlapping shifts for each assignment
   - **Line 348-350:** Query other shifts for rest period check
   - **Line 386-388:** Query shifts for weekly hours
   - **Line 502-504:** Query shifts for consecutive days
   - **Proposal:** Preload all context in `validate_weekly_schedule()`:
     - Users by IDs
     - Shifts by IDs
     - Time-off by (user_id, date ranges)
     - Roles cache
     - Constraints cache (already loaded in `__init__`)

### 🟢 Modularity

1. **Consider dataclasses for ValidationError/ValidationResult**

   - Currently manual classes (fine, but dataclass would be cleaner)
   - Already has `to_dict()` methods, dataclass could provide this

2. **Provide a bulk-validation API that accepts preloaded context**

   - Create `validate_assignments_bulk(assignments, preloaded_context)` method
   - Preloaded context contains: users_dict, shifts_dict, time_off_map, roles_dict
   - Reduces DB queries and improves testability

3. **Extract time normalization to shared utility**
   - Duplicates logic from precompute module
   - Should use same `normalize_shift_datetimes()` function

### Proposed changes

- Fix `_times_overlap()` to use full datetime comparison
- Remove date filter in `_check_shift_overlaps()` or use datetime range overlap
- Fix `_calculate_shift_hours()` to handle overnight shifts
- Fix `_calculate_hours_between_shifts()` to compute rest as `(later.start - earlier.end)`
- Refactor `validate_weekly_schedule()` to batch-load all context upfront
- Add bulk validation API with preloaded context

---

## File 5 – schedulingService.py (MIP solver)

### 🔴 CRITICAL correctness issues (large section)

1. **Role coverage is fundamentally incorrect with x[i,j] (no role dimension)**

   **Problem:** The MIP model uses decision variables `x[i,j]` (employee i, shift j) but constraints require per-role coverage.

   **Current implementation (lines 217-260):**

   - Creates `x[i,j]` only if employee i is eligible for at least one role of shift j
   - Coverage constraint (line 248-260): For each role r required by shift j, sums `x[i,j]` for all employees i who have role r
   - **Critical flaw:** If an employee has multiple roles, the same `x[i,j]` variable is counted for multiple roles

   **Example:**

   - Shift j requires: Role A (count=1), Role B (count=1)
   - Employee i has both roles A and B
   - Constraint for Role A: `x[i,j] == 1` (employee i assigned)
   - Constraint for Role B: `x[i,j] == 1` (same variable!)
   - **Result:** One employee satisfies both role requirements, but only one `x[i,j]` variable exists
   - **Post-solve (line 388):** Assigns "first matching role" arbitrarily

   **Impact:** The model can produce solutions where:

   - Coverage appears satisfied in constraints
   - But post-solve role assignment doesn't match actual coverage needs
   - If shift needs 2 different roles, but only 1 employee with both roles is assigned, the solution is invalid

   **Fix:** Must model `x[i,j,r]` (employee i, shift j, role r) OR use an equivalent role-aware formulation.

2. **Coverage constraints missing when no eligible employees**

   **Problem (line 258):** `if eligible_employees:` skips constraint if list is empty

   **Current logic:**

   ```python
   if eligible_employees:
       model += mip.xsum(eligible_employees) == required_count, ...
   ```

   **Impact:** If a shift requires Role A (count=2) but no employees have Role A:

   - Constraint is skipped
   - Model can produce "solutions" that ignore this requirement
   - Solution status may be "FEASIBLE" or "OPTIMAL" but coverage is incomplete

   **Fix:** Must enforce infeasibility:

   ```python
   if not eligible_employees:
       if required_count > 0:
           # Add impossible constraint: 0 == required_count
           model += 0 == required_count, f'infeasible_coverage_shift_{j}_role_{role_id}'
   else:
       model += mip.xsum(eligible_employees) == required_count, ...
   ```

   OR use slack variables with high penalty in objective.

3. **Fairness variables mismatch**

   **Problem (lines 295-323):**

   - `assignments_per_employee` only includes employees who have at least one variable (line 297-299)
   - But fairness deviation uses `enumerate(assignments_per_employee)` treating index `i` as employee index (line 313)
   - **Example:** If employees 0, 2, 5 have variables, `assignments_per_employee = [emp0_total, emp2_total, emp5_total]`
   - `enumerate()` gives indices 0, 1, 2, but code treats them as employee indices 0, 2, 5
   - **Impact:** Fairness deviation is computed for wrong employees, or crashes if accessing `data.employees[i]`

   **Fix:** Build `emp_total` for every employee in `range(n_employees)`:

   ```python
   assignments_per_employee = []
   for i in range(n_employees):
       emp_vars = [x[i, j] for j in range(n_shifts) if (i, j) in x]
       emp_total = mip.xsum(emp_vars) if emp_vars else 0
       assignments_per_employee.append(emp_total)
   ```

4. **Overlap constraints rely on shift_overlaps which is currently wrong for overnight**

   **Problem (line 265):** Uses `data.shift_overlaps` which comes from precompute (has overnight bug)

   **Impact:** Overlap constraints may miss overlaps for overnight shifts, allowing invalid assignments

5. **Clearing assignments unconditionally**

   **Problem (lines 117-128):** Deletes all assignments for schedule unconditionally

   **Current logic:**

   ```python
   self.db.query(ShiftAssignmentModel).filter(
       ShiftAssignmentModel.planned_shift_id.in_(shift_ids)
   ).delete(synchronize_session=False)
   ```

   **Issues:**

   - No transaction safety (if solver fails after delete, assignments are lost)
   - No option to preserve existing assignments
   - Should clarify: is this intended behavior or should we preserve preferred assignments?

   **Recommendation:**

   - Wrap in transaction
   - Or preserve assignments marked as "preferred" (from `data.existing_assignments`)

6. **ConstraintService not integrated**

   **Problem:** ConstraintService exists but is never called to validate the solution

   **Current flow:**

   - Build MIP model with constraints
   - Solve
   - Extract assignments
   - **Missing:** Validate solution with ConstraintService before committing

   **Decision needed:**

   - Option A: Model all constraints in MIP (current approach, but incomplete)
   - Option B: Validate post-solve and iterate/repair if violations found
   - Option C: Hybrid (hard constraints in MIP, soft constraints validated post-solve)

   **Recommendation:** At minimum, validate post-solve and log warnings for soft constraint violations

### 🟠 Efficiency issues

1. **No-overlap constraints: iterating overlap pairs × employees can blow up**

   **Problem (lines 274-278):** For each overlap pair (shift_idx, overlapping_idx), iterate all employees

   **Current:** O(E × O) where O = number of overlap pairs

   - If many shifts overlap, this creates many constraints
   - Each constraint: `x[i, shift_idx] + x[i, overlapping_idx] <= 1`

   **Suggestion:**

   - Generate constraints once per unordered pair `(shift_idx, overlapping_idx)`
   - Use a set to track already-processed pairs to avoid duplicates
   - Current code processes both directions (line 265-278), but each pair is processed twice

### 🟢 Proposed refactor plan

**Step 1: Create decision vars x[i,j,r] only for eligible triples**

```python
x = {}
for i, emp in enumerate(data.employees):
    for j, shift in enumerate(data.shifts):
        if data.availability_matrix[i, j] != 1:
            continue
        required_roles = shift.get('required_roles') or []
        emp_roles = set(emp.get('roles') or [])
        for role_req in required_roles:
            role_id = role_req['role_id']
            if role_id in emp_roles:
                x[i, j, role_id] = model.add_var(var_type=mip.BINARY, name=f'x_{i}_{j}_{role_id}')
```

**Step 2: Coverage: sum_i x[i,j,r] == required_count[j,r]**

```python
for j, shift in enumerate(data.shifts):
    for role_req in shift['required_roles']:
        role_id = role_req['role_id']
        required_count = role_req['required_count']
        eligible_vars = [x[i, j, role_id] for i in range(n_employees) if (i, j, role_id) in x]
        if not eligible_vars:
            if required_count > 0:
                model += 0 == required_count, f'infeasible_coverage_shift_{j}_role_{role_id}'
        else:
            model += mip.xsum(eligible_vars) == required_count, f'coverage_shift_{j}_role_{role_id}'
```

**Step 3: Single role per employee per shift: sum_r x[i,j,r] <= 1**

```python
for i in range(n_employees):
    for j in range(n_shifts):
        role_vars = [x[i, j, r] for r in all_roles if (i, j, r) in x]
        if len(role_vars) > 1:
            model += mip.xsum(role_vars) <= 1, f'single_role_emp_{i}_shift_{j}'
```

**Step 4: Extraction yields role directly (no "pick first role")**

```python
for (i, j, role_id), var in x.items():
    if var.x > 0.5:
        assignments.append({
            'user_id': data.employees[i]['user_id'],
            'planned_shift_id': data.shifts[j]['planned_shift_id'],
            'role_id': role_id,  # Direct from variable
            'preference_score': float(data.preference_scores[i, j])
        })
```

**Additional changes:**

- Fix fairness variable indexing (build for all employees)
- Add infeasibility check when no eligible employees
- Integrate ConstraintService validation post-solve
- Fix overlap constraints to use corrected precompute logic
- Add transaction safety for assignment clearing

---

## Prioritized Fix List (Actionable)

### 1. 🔴 CRITICAL: Fix overnight shift normalization (overlap + duration)

**Files:** optimization_precompute.py, optimization_data_builder.py, constraintService.py  
**Risk:** High (affects correctness for night shifts)  
**Impact:** High (multiple modules affected)  
**Effort:** Medium (2-3 hours)  
**Steps:**

- Create `normalize_shift_datetimes()` in precompute module
- Update `_shifts_overlap()` to use normalization
- Update `build_shift_durations()` to use normalization
- Update `_calculate_time_overlap()` in builder to handle overnight
- Update `_times_overlap()` in validator to use datetime comparison
- Update `_calculate_shift_hours()` to handle overnight
- Test with overnight shift examples

### 2. 🔴 CRITICAL: Change MIP to role-aware variables x[i,j,r]

**Files:** schedulingService.py  
**Risk:** Critical (fundamental model flaw)  
**Impact:** Critical (solutions may be invalid)  
**Effort:** High (4-6 hours)  
**Steps:**

- Refactor decision variables to `x[i,j,r]`
- Update coverage constraints to use role dimension
- Add single-role-per-shift constraint
- Update objective function to use role-aware variables
- Update solution extraction to use role from variable
- Test with multi-role scenarios

### 3. 🔴 CRITICAL: Add infeasibility check when no eligible employees

**Files:** schedulingService.py  
**Risk:** High (allows invalid solutions)  
**Impact:** High (coverage requirements ignored)  
**Effort:** Low (30 minutes)  
**Steps:**

- Add check in coverage constraint: if no eligible employees and required_count > 0, add impossible constraint
- Or use slack variables with high penalty
- Test with scenario where no employees have required role

### 4. 🟠 MAJOR: Unify role requirement schema across DTO/builder/solver

**Files:** optimization_data.py, optimization_data_builder.py  
**Risk:** Medium (confusion, potential bugs)  
**Impact:** Medium (schema inconsistency)  
**Effort:** Low (1 hour)  
**Steps:**

- Decide on single schema: either `List[int]` or `List[Dict]` with counts
- Update `OptimizationData.role_requirements` to match
- Update `build_role_requirements()` to preserve counts if needed
- Update documentation
- Remove unused `role_requirements` if solver uses shift dicts directly

### 5. 🟠 MAJOR: Fix rest-hours math + cross-day overlap in validator

**Files:** constraintService.py  
**Risk:** Medium (incorrect validation)  
**Impact:** Medium (rest period violations missed)  
**Effort:** Medium (2 hours)  
**Steps:**

- Fix `_calculate_hours_between_shifts()` to compute `(later.start - earlier.end)`
- Return negative if overlap detected
- Fix `_check_shift_overlaps()` to remove date filter or use datetime range
- Fix `_times_overlap()` to use full datetime comparison
- Test with overnight shifts and cross-day overlaps

### 6. 🟠 MAJOR: Batch DB loads in weekly validation

**Files:** constraintService.py  
**Risk:** Low (performance only)  
**Impact:** High (N+1 query problem)  
**Effort:** Medium (2-3 hours)  
**Steps:**

- Preload all users by IDs in `validate_weekly_schedule()`
- Preload all shifts by IDs
- Preload time-off by (user_id, date ranges)
- Preload roles cache
- Pass preloaded context to `validate_assignment()` or refactor to bulk validation
- Test with large schedules

### 7. 🟠 MAJOR: Fix availability matrix to match docstring or update docstring

**Files:** optimization_data_builder.py  
**Risk:** Low (documentation mismatch)  
**Impact:** Medium (confusion, potential bugs)  
**Effort:** Low (1 hour)  
**Steps:**

- Either: Add overlap check with existing assignments in availability matrix
- Or: Update docstring to remove claim about overlap checking
- Use precomputed `time_off_conflicts` instead of recomputing
- Test availability matrix correctness

### 8. 🟠 MAJOR: Fix fairness variable indexing mismatch

**Files:** schedulingService.py  
**Risk:** Medium (incorrect fairness calculation or crash)  
**Impact:** Medium (fairness objective wrong)  
**Effort:** Low (30 minutes)  
**Steps:**

- Build `emp_total` for all employees in `range(n_employees)`
- Use employee index correctly in fairness calculation
- Test fairness calculation with sparse assignments

### 9. 🟢 MINOR: Optimize availability matrix computation

**Files:** optimization_data_builder.py  
**Risk:** Low (performance only)  
**Impact:** Low (efficiency improvement)  
**Effort:** Low (1 hour)  
**Steps:**

- Precompute `required_role_ids_per_shift` once
- Use precomputed `time_off_conflicts` instead of triple-nested loop
- Filter preferences query to relevant employees only
- Test performance improvement

### 10. 🟢 MINOR: Add validation to OptimizationData

**Files:** optimization_data.py  
**Risk:** Low (runtime errors caught earlier)  
**Impact:** Low (better error messages)  
**Effort:** Low (30 minutes)  
**Steps:**

- Add `validate()` method to check all required fields are set
- Add shape/dtype checks for numpy arrays
- Call validation in builder before returning data
- Test with incomplete data

---

## Additional Recommendations

1. **Add integration tests** for overnight shifts, multi-role scenarios, and edge cases
2. **Add unit tests** for time normalization functions
3. **Consider using Pydantic** for OptimizationData to get automatic validation
4. **Document timezone assumptions** (currently assumes naive datetimes)
5. **Add logging** for constraint violations in MIP model
6. **Consider constraint relaxation** for soft constraints (use slack variables)
7. **Add metrics** for constraint satisfaction in solution (how many constraints satisfied/violated)
