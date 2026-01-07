# Code Review: Services Layer (`app/services/`)

**Date:** 2024  
**Scope:** All files under `app/services/` including subdirectories  
**Goal:** Make services layer clean, thin, and maintainable

---

## 1. Executive Summary

### Biggest Problems and Highest ROI Fixes

1. **🔴 Duplicate datetime normalization logic** - Same logic exists in `constraintService.py` and `optimization_precompute.py`, leading to maintenance burden and potential inconsistencies.

2. **🔴 Transaction safety issues** - `SchedulingPersistence.clear_existing_assignments()` doesn't commit, but if called without proper transaction management, partial deletes can leave DB inconsistent.

3. **🟠 Large orchestration methods** - `scheduling_service._execute_run()` (134 lines) and `optimization_data_builder.build()` (76 lines) do too many things, violating SRP.

4. **🟠 Duplicate shift overlap detection** - Overlap detection logic exists in both `constraintService._check_shift_overlaps()` and `optimization_precompute.build_shift_overlaps()`, with slight differences.

5. **🟠 Inconsistent naming** - `schedulingService.py` (backward compat wrapper) vs `scheduling_service.py` (actual implementation) creates confusion.

6. **🟡 Missing transaction boundaries** - Some operations commit individually when they should be atomic (e.g., run creation + status updates in `optimize_schedule()`).

7. **🟡 Performance: Repeated queries** - `constraintService._load_system_constraints()` called on init, but constraints may change. No caching strategy.

8. **🟡 Inconsistent error handling** - Some methods catch and re-raise with context, others let exceptions bubble up raw.

9. **🟡 Magic numbers and hardcoded values** - Soft penalty weight (100.0) in `mip_solver._build_objective()`, default preference score (0.5) in `optimization_data_builder.build_preference_scores()`.

10. **🟢 Print statements instead of logging** - Multiple `print()` calls in production code should use proper logging.

---

## 2. Prioritized Issue List

### 🔴 Critical (Correctness/Data Corruption)

#### CRIT-1: Duplicate Datetime Normalization Logic

**Files:**

- `constraintService.py:538-564` (`_normalize_shift_datetimes`)
- `optimization_precompute.py:12-50` (`normalize_shift_datetimes`)

**Problem:**
Two implementations of the same logic with subtle differences:

- `constraintService` version handles `PlannedShiftModel` objects
- `optimization_precompute` version handles dictionaries
- Both handle overnight shifts, but edge cases may differ
- Maintenance burden: changes must be made in two places

**Fix:**

- Extract to shared utility module: `app/services/utils/datetime_utils.py`
- Create unified function that accepts both model objects and dicts
- Update both callers to use shared utility
- Add comprehensive tests for edge cases (overnight, cross-day, timezone)

**Risk:** Low (refactor only, no behavior change)

---

#### CRIT-2: Transaction Safety in Persistence Layer

**File:** `scheduling/persistence.py:26-46` (`clear_existing_assignments`)

**Problem:**

```python
def clear_existing_assignments(self, weekly_schedule_id: int) -> None:
    # ... deletes assignments ...
    # No commit - designed to be part of larger transaction
```

- If called without proper transaction management, partial deletes can occur
- If exception happens after delete but before commit, DB is inconsistent
- No rollback handling if called in wrong context

**Fix:**

- Add explicit transaction context manager or require caller to manage transactions
- Document transaction requirements clearly
- Consider making it a context manager or requiring `commit=False` parameter
- Add validation that we're in a transaction

**Risk:** Medium (requires careful testing of transaction boundaries)

---

#### CRIT-3: Inconsistent Error Handling in Run Execution

**File:** `scheduling/scheduling_service.py:72-80, 95-103`

**Problem:**

- `optimize_schedule()` catches `Exception`, updates run status, commits, then re-raises
- `_execute_optimization_for_run()` does the same
- If commit fails, run status may be inconsistent
- Generic `Exception` catches too much (including programming errors)

**Fix:**

- Catch specific exceptions (ValueError, SQLAlchemyError, etc.)
- Use transaction rollback on error
- Consider using database savepoints for nested transactions
- Log errors with full context before re-raising

**Risk:** Medium (requires testing error paths)

---

#### CRIT-4: Potential Race Condition in Run Status Updates

**File:** `scheduling/scheduling_service.py:120-124`

**Problem:**

```python
run.status = SchedulingRunStatus.RUNNING
if not run.started_at:
    run.started_at = datetime.now()
self.db.commit()
```

- If multiple processes try to update the same run, race condition possible
- No optimistic locking or version checks

**Fix:**

- Add version column to `SchedulingRunModel` for optimistic locking
- Or use database-level locking (SELECT FOR UPDATE)
- Or ensure only one process can update a run at a time

**Risk:** Low (only affects concurrent access scenarios)

---

### 🟠 High (Architecture/Design/Maintainability)

#### HIGH-1: Large Orchestration Method Violates SRP

**File:** `scheduling/scheduling_service.py:105-238` (`_execute_run`)

**Problem:**

- 134 lines doing: status updates, config loading, data building, solving, validation, persistence, commit
- Hard to test individual pieces
- Hard to reuse parts (e.g., validation without persistence)

**Fix:**

- Extract into smaller methods:
  - `_load_optimization_config(run)` -> config
  - `_build_and_solve(data_builder, config)` -> solution
  - `_validate_solution(solution, constraint_service, weekly_schedule_id)` -> validation_result
  - `_persist_solution(run, solution, apply_assignments)` -> void
- Keep `_execute_run()` as thin orchestrator

**Risk:** Low (refactor, behavior unchanged)

---

#### HIGH-2: Duplicate Shift Overlap Detection

**Files:**

- `constraintService.py:279-319` (`_check_shift_overlaps`)
- `optimization_precompute.py:75-106` (`build_shift_overlaps`)

**Problem:**

- Two different implementations:
  - `constraintService` checks overlaps for validation (uses existing assignments)
  - `optimization_precompute` builds overlap graph for MIP model
- Both use datetime normalization (see CRIT-1)
- Logic is similar but not identical

**Fix:**

- Extract overlap detection to shared utility
- Make it configurable: return graph vs. check specific pairs
- Both services use shared utility
- Consolidate datetime normalization (see CRIT-1)

**Risk:** Low (refactor, but need to ensure both use cases work)

---

#### HIGH-3: Inconsistent Naming Convention

**Files:**

- `schedulingService.py` (backward compat wrapper)
- `scheduling_service.py` (actual implementation)

**Problem:**

- Python convention is `snake_case` for modules
- `schedulingService.py` uses `camelCase`
- Creates confusion about which file to import from

**Fix:**

- Rename `schedulingService.py` to `scheduling_service_legacy.py` or remove it
- Update all imports to use `scheduling_service.py` directly
- Add deprecation notice if keeping wrapper temporarily

**Risk:** Low (but requires updating all imports)

---

#### HIGH-4: Large Data Builder Method

**File:** `optimization_data_services/optimization_data_builder.py:52-136` (`build`)

**Problem:**

- 76 lines orchestrating many steps
- Hard to test individual data extraction steps
- Hard to add new data sources

**Fix:**

- Extract into smaller methods:
  - `_extract_base_data(weekly_schedule_id)` -> employees, shifts, roles
  - `_build_indices(employees, shifts)` -> employee_index, shift_index
  - `_build_matrices(employees, shifts, ...)` -> availability, preferences
  - `_build_constraints_and_conflicts(...)` -> system_constraints, overlaps, rest_conflicts
- Keep `build()` as thin orchestrator

**Risk:** Low (refactor only)

---

#### HIGH-5: Missing Type Hints in Some Methods

**Files:**

- `constraintService.py:566-584` (`_times_overlap` - complex signature)
- `optimization_data_builder.py:616-663` (helper methods)

**Problem:**

- Some methods have incomplete or missing type hints
- Makes code harder to understand and maintain
- IDE autocomplete suffers

**Fix:**

- Add complete type hints to all public and internal methods
- Use `typing.Protocol` for duck-typed parameters
- Add `# type: ignore` only when necessary with explanation

**Risk:** Low (additive change)

---

#### HIGH-6: System Constraints Cached on Init

**File:** `constraintService.py:100-109` (`_load_system_constraints`)

**Problem:**

- Constraints loaded once in `__init__`
- If constraints change in DB, service instance has stale data
- No invalidation or refresh mechanism

**Fix:**

- Load constraints on-demand (lazy loading)
- Or add `refresh_constraints()` method
- Or use a cache with TTL
- Document caching behavior

**Risk:** Low (but may affect performance if called frequently)

---

#### HIGH-7: Inconsistent Return Types

**File:** `scheduling/scheduling_service.py:38-80`

**Problem:**

- `optimize_schedule()` returns `Tuple[SchedulingRunModel, SchedulingSolution]`
- `_execute_optimization_for_run()` returns nothing (void)
- Inconsistent API makes it hard to compose operations

**Fix:**

- Standardize return types across similar methods
- Consider returning a result object instead of tuple
- Document return types clearly

**Risk:** Low (but may require updating callers)

---

### 🟡 Medium (Cleanup/Refactor)

#### MED-1: Magic Numbers and Hardcoded Values

**Files:**

- `mip_solver.py:520` - `soft_penalty_weight = 100.0`
- `optimization_data_builder.py:517` - default preference score `0.5`
- `optimization_data_builder.py:554-567` - preference score weights (1.0, 0.8, 0.6)

**Problem:**

- Magic numbers scattered throughout code
- Hard to tune without code changes
- No documentation of why these values were chosen

**Fix:**

- Extract to configuration constants at module level
- Or move to `OptimizationConfigModel` if they should be user-configurable
- Document rationale for each value
- Consider making them configurable via config

**Risk:** Low (additive change)

---

#### MED-2: Code Duplication in Validation Methods

**File:** `constraintService.py:372-534`

**Problem:**

- `_check_weekly_hours()`, `_check_weekly_shifts()`, `_check_consecutive_days()` all:
  - Query user by ID
  - Get constraint from `system_constraints`
  - Check if hard/soft
  - Build error message
  - Add to result
- Similar patterns repeated

**Fix:**

- Extract helper: `_check_constraint_with_user(user_id, constraint_type, get_value_func, error_builder_func)`
- Or use a constraint checker registry pattern
- Reduce duplication while keeping methods readable

**Risk:** Low (refactor only)

---

#### MED-3: Print Statements Instead of Logging

**Files:**

- `scheduling/scheduling_service.py` - multiple `print()` calls
- `scheduling/mip_solver.py` - multiple `print()` calls

**Problem:**

- Print statements can't be filtered, formatted, or redirected
- No log levels (DEBUG, INFO, WARNING)
- Hard to debug in production

**Fix:**

- Replace all `print()` with proper logging
- Use appropriate log levels
- Add structured logging with context (run_id, schedule_id, etc.)

**Risk:** Low (additive change)

---

#### MED-4: Missing Docstrings in Helper Methods

**Files:**

- `optimization_data_builder.py:616-663` (helper methods)
- `constraintService.py:536-619` (helper methods)

**Problem:**

- Some helper methods lack docstrings
- Makes code harder to understand
- Inconsistent with rest of codebase

**Fix:**

- Add docstrings to all helper methods
- Include Args, Returns, Raises sections
- Document edge cases (e.g., overnight shifts)

**Risk:** Low (additive change)

---

#### MED-5: Inefficient Query Patterns

**File:** `constraintService.py:233-253` (`_check_time_off_conflicts`)

**Problem:**

- Queries time-off requests per employee per shift validation
- If validating many assignments, this is N+1 query pattern
- Should batch queries

**Fix:**

- Batch load all time-off requests for all employees in one query
- Build lookup map once
- Reuse in validation loop

**Risk:** Low (performance improvement)

---

#### MED-6: Inconsistent Error Messages

**Files:**

- `scheduling/run_status.py:50-72` (`build_error_message`)
- `scheduling/scheduling_service.py:177-190` (validation error messages)

**Problem:**

- Error messages built in different places with different formats
- Some are user-friendly, others are technical
- No consistent error message structure

**Fix:**

- Create error message builder utility
- Standardize error message format
- Separate user-facing vs. developer-facing messages

**Risk:** Low (additive change)

---

### 🟢 Low (Style/Nits)

#### LOW-1: Unused Imports

**Files:**

- `constraintService.py:11` - `and_, or_` from sqlalchemy (not used)
- `optimization_data_builder.py:12` - `select` imported but could use query API

**Fix:**

- Remove unused imports
- Run linter to catch these automatically

**Risk:** None

---

#### LOW-2: Inconsistent String Formatting

**Files:**

- Mix of f-strings, `.format()`, and `%` formatting

**Fix:**

- Standardize on f-strings (Python 3.6+)
- Update all string formatting

**Risk:** None

---

#### LOW-3: Long Lines

**Files:**

- Some lines exceed 100 characters

**Fix:**

- Break long lines appropriately
- Use black or similar formatter

**Risk:** None

---

#### LOW-4: Missing Type Hints in Some Places

**Files:**

- Some internal methods lack return type hints

**Fix:**

- Add return type hints everywhere
- Use `-> None` for void methods

**Risk:** None

---

## 3. Proposed Target Architecture

### Ideal Directory Structure

```
app/services/
├── __init__.py
│
├── scheduling/                    # Scheduling optimization domain
│   ├── __init__.py
│   ├── orchestrator.py           # Main SchedulingService (thin)
│   ├── solver/                    # MIP solver domain
│   │   ├── __init__.py
│   │   ├── mip_builder.py        # Model building logic
│   │   ├── mip_solver.py         # Solver wrapper
│   │   └── solution_extractor.py # Extract assignments from model
│   ├── validation/                # Validation domain
│   │   ├── __init__.py
│   │   ├── constraint_validator.py  # ConstraintService (renamed)
│   │   └── validators/            # Individual validators
│   │       ├── time_off_validator.py
│   │       ├── overlap_validator.py
│   │       └── weekly_constraints_validator.py
│   ├── persistence/              # Persistence domain
│   │   ├── __init__.py
│   │   ├── run_persistence.py   # SchedulingRun operations
│   │   └── assignment_persistence.py  # ShiftAssignment operations
│   ├── metrics.py                 # Solution metrics (unchanged)
│   ├── run_status.py             # Status mapping (unchanged)
│   └── types.py                  # Shared types (unchanged)
│
├── optimization_data/             # Data preparation domain
│   ├── __init__.py
│   ├── data_builder.py           # Main orchestrator (thin)
│   ├── extractors/                # Data extraction
│   │   ├── employee_extractor.py
│   │   ├── shift_extractor.py
│   │   └── constraint_extractor.py
│   ├── precompute/                # Derived data computation
│   │   ├── overlaps.py            # Shift overlap detection
│   │   ├── durations.py          # Shift duration calculation
│   │   ├── conflicts.py          # Time-off and rest conflicts
│   │   └── matrices.py           # Availability and preference matrices
│   └── types.py                   # OptimizationData (unchanged)
│
└── utils/                         # Shared utilities
    ├── __init__.py
    ├── datetime_utils.py          # Datetime normalization (from CRIT-1)
    ├── overlap_utils.py           # Overlap detection (from HIGH-2)
    └── error_utils.py             # Error message building (from MED-6)
```

### What Belongs Where

**Orchestrators:**

- `scheduling/orchestrator.py` - Coordinates solver, validation, persistence
- `optimization_data/data_builder.py` - Coordinates extractors and precompute

**Pure Domain Logic (No DB):**

- `scheduling/solver/*` - MIP model building and solving
- `scheduling/validation/validators/*` - Individual constraint validators
- `optimization_data/precompute/*` - Derived data computation
- `utils/*` - Pure utility functions

**Persistence (DB Access Only):**

- `scheduling/persistence/*` - All database writes
- `optimization_data/extractors/*` - All database reads

**Boundaries:**

- Orchestrators depend on domain logic and persistence
- Domain logic has NO database dependencies
- Persistence has NO business logic
- Utils have NO dependencies on domain models

---

## 4. Refactor Plan (Safe, Incremental)

### Phase 1: Extract Shared Utilities (Low Risk)

**Goal:** Eliminate duplicate datetime normalization and overlap detection

1. **Create `app/services/utils/` directory**

   - Add `datetime_utils.py` with unified `normalize_shift_datetimes()`
   - Add `overlap_utils.py` with unified overlap detection
   - Add tests for edge cases

2. **Update callers**

   - Update `constraintService.py` to use shared utils
   - Update `optimization_precompute.py` to use shared utils
   - Run tests to ensure behavior unchanged

3. **Test:** All existing tests pass, no behavior changes

**Estimated Time:** 2-3 hours

---

### Phase 2: Improve Transaction Safety (Medium Risk)

**Goal:** Ensure all database operations are transaction-safe

1. **Add transaction context manager**

   - Create `TransactionManager` utility
   - Or use SQLAlchemy's built-in transaction handling

2. **Update persistence layer**

   - Make `clear_existing_assignments()` explicitly require transaction
   - Add rollback handling in `persist_solution_and_apply_assignments()`
   - Document transaction requirements

3. **Update orchestrator**

   - Ensure `_execute_run()` uses proper transaction boundaries
   - Add savepoints for nested operations if needed

4. **Test:**
   - Test error scenarios (commit failures, rollbacks)
   - Test concurrent access scenarios
   - Integration tests for transaction boundaries

**Estimated Time:** 4-6 hours

---

### Phase 3: Split Large Methods (Low Risk)

**Goal:** Break down `_execute_run()` and `build()` into smaller, testable pieces

1. **Refactor `scheduling_service._execute_run()`**

   - Extract `_load_optimization_config()`
   - Extract `_build_and_solve()`
   - Extract `_validate_solution()`
   - Extract `_persist_solution()`
   - Keep `_execute_run()` as thin orchestrator

2. **Refactor `optimization_data_builder.build()`**

   - Extract `_extract_base_data()`
   - Extract `_build_indices()`
   - Extract `_build_matrices()`
   - Extract `_build_constraints_and_conflicts()`
   - Keep `build()` as thin orchestrator

3. **Test:**
   - Unit tests for each extracted method
   - Integration tests for full flow
   - Ensure behavior unchanged

**Estimated Time:** 6-8 hours

---

### Phase 4: Standardize Error Handling (Low Risk)

**Goal:** Consistent error handling and logging

1. **Replace print statements with logging**

   - Set up logging configuration
   - Replace all `print()` calls
   - Add structured logging with context

2. **Standardize error messages**

   - Create error message builder utility
   - Update all error message construction
   - Separate user-facing vs. developer messages

3. **Improve exception handling**

   - Catch specific exceptions instead of generic `Exception`
   - Add proper error context
   - Ensure rollbacks on errors

4. **Test:**
   - Test error paths
   - Verify log output
   - Check error messages are user-friendly

**Estimated Time:** 4-5 hours

---

### Phase 5: Extract Configuration Constants (Low Risk)

**Goal:** Remove magic numbers

1. **Create configuration module**

   - `app/services/config.py` or add to existing config
   - Extract all magic numbers
   - Document rationale

2. **Update callers**

   - Replace magic numbers with constants
   - Consider making some user-configurable

3. **Test:**
   - Verify behavior unchanged
   - Test with different config values

**Estimated Time:** 2-3 hours

---

### Phase 6: Improve Type Safety (Low Risk)

**Goal:** Complete type hints everywhere

1. **Add missing type hints**

   - All public methods
   - All internal methods
   - All return types

2. **Run type checker**

   - Use mypy or similar
   - Fix all type errors
   - Add type: ignore only when necessary

3. **Test:**
   - Verify code still works
   - Check IDE autocomplete works

**Estimated Time:** 3-4 hours

---

### Phase 7: Optimize Query Patterns (Low Risk)

**Goal:** Eliminate N+1 queries

1. **Identify N+1 patterns**

   - Review all database queries
   - Find repeated queries in loops

2. **Batch queries**

   - Load all needed data upfront
   - Build lookup maps
   - Use in loops

3. **Test:**
   - Performance tests
   - Verify behavior unchanged
   - Check query counts

**Estimated Time:** 4-6 hours

---

### Phase 8: Reorganize Directory Structure (Medium Risk)

**Goal:** Implement target architecture

1. **Create new directory structure**

   - Create new directories per target architecture
   - Move files incrementally

2. **Update imports**

   - Update all imports to new locations
   - Update `__init__.py` files
   - Keep backward compatibility if needed

3. **Test:**
   - All tests pass
   - No import errors
   - Behavior unchanged

**Estimated Time:** 8-12 hours

---

## 5. Quick Wins Checklist

These changes can be done immediately with minimal risk:

### Immediate (Can do now)

- [ ] **Remove unused imports** (LOW-1)

  - Files: `constraintService.py`, `optimization_data_builder.py`
  - Run linter, remove unused imports
  - **Time:** 15 minutes

- [ ] **Add missing return type hints** (LOW-4)

  - Add `-> None` to void methods
  - Add return types to helper methods
  - **Time:** 1 hour

- [ ] **Standardize string formatting to f-strings** (LOW-2)

  - Replace `.format()` and `%` with f-strings
  - **Time:** 30 minutes

- [ ] **Add docstrings to helper methods** (MED-4)

  - `optimization_data_builder.py:616-663`
  - `constraintService.py:536-619`
  - **Time:** 2 hours

- [ ] **Extract magic numbers to constants** (MED-1)
  - Create `app/services/constants.py`
  - Move soft_penalty_weight, default_preference_score, etc.
  - **Time:** 1 hour

### This Week (Low risk, high value)

- [ ] **Extract datetime normalization utility** (CRIT-1)

  - Create `app/services/utils/datetime_utils.py`
  - Update both callers
  - **Time:** 2-3 hours

- [ ] **Replace print statements with logging** (MED-3)

  - Set up logging config
  - Replace all print() calls
  - **Time:** 2-3 hours

- [ ] **Extract overlap detection utility** (HIGH-2)

  - Create `app/services/utils/overlap_utils.py`
  - Update both callers
  - **Time:** 2-3 hours

- [ ] **Split `_execute_run()` method** (HIGH-1)
  - Extract 4-5 smaller methods
  - Keep orchestrator thin
  - **Time:** 4-6 hours

### This Month (Medium risk, architectural)

- [ ] **Improve transaction safety** (CRIT-2)

  - Add transaction context manager
  - Update persistence layer
  - **Time:** 4-6 hours

- [ ] **Split `build()` method** (HIGH-4)

  - Extract smaller methods
  - **Time:** 4-6 hours

- [ ] **Optimize query patterns** (MED-5)

  - Batch time-off queries
  - Batch user queries in validation
  - **Time:** 4-6 hours

- [ ] **Rename schedulingService.py** (HIGH-3)
  - Update all imports
  - Remove backward compat if not needed
  - **Time:** 2-3 hours

---

## 6. Proposed PR-Sized Refactors

### PR #1: Extract Shared Datetime and Overlap Utilities

**Scope:** Create `app/services/utils/` with shared utilities  
**Files Changed:**

- New: `app/services/utils/__init__.py`
- New: `app/services/utils/datetime_utils.py`
- New: `app/services/utils/overlap_utils.py`
- Modified: `constraintService.py` (use shared utils)
- Modified: `optimization_precompute.py` (use shared utils)

**Testing:**

- Unit tests for utilities
- Integration tests for constraint service
- Integration tests for optimization data builder

**Risk:** Low (refactor only, no behavior change)

---

### PR #2: Improve Transaction Safety in Persistence Layer

**Scope:** Add explicit transaction management  
**Files Changed:**

- Modified: `scheduling/persistence.py` (add transaction context)
- Modified: `scheduling/scheduling_service.py` (use transaction context)
- New: `scheduling/persistence/transaction.py` (transaction manager)

**Testing:**

- Test error scenarios (rollback on failure)
- Test concurrent access
- Integration tests for full flow

**Risk:** Medium (requires careful testing)

---

### PR #3: Split Large Orchestration Methods

**Scope:** Break down `_execute_run()` and `build()`  
**Files Changed:**

- Modified: `scheduling/scheduling_service.py` (extract methods)
- Modified: `optimization_data_services/optimization_data_builder.py` (extract methods)

**Testing:**

- Unit tests for each extracted method
- Integration tests for full flow
- Ensure behavior unchanged

**Risk:** Low (refactor only)

---

### PR #4: Replace Print Statements with Logging

**Scope:** Standardize logging across services  
**Files Changed:**

- Modified: `scheduling/scheduling_service.py`
- Modified: `scheduling/mip_solver.py`
- New/Modified: `app/core/logging_config.py` (if needed)

**Testing:**

- Verify log output in tests
- Check log levels are appropriate
- Ensure no performance regression

**Risk:** Low (additive change)

---

### PR #5: Extract Configuration Constants and Improve Type Hints

**Scope:** Remove magic numbers and complete type hints  
**Files Changed:**

- New: `app/services/constants.py`
- Modified: `scheduling/mip_solver.py` (use constants)
- Modified: `optimization_data_services/optimization_data_builder.py` (use constants)
- Modified: All service files (add type hints)

**Testing:**

- Run type checker (mypy)
- Verify behavior unchanged
- Check IDE autocomplete

**Risk:** Low (additive changes)

---

## 7. Testing Strategy

After each refactor phase:

1. **Unit Tests**

   - Test each extracted method independently
   - Test edge cases (overnight shifts, empty data, etc.)
   - Test error paths

2. **Integration Tests**

   - Test full optimization flow
   - Test validation flow
   - Test persistence flow

3. **Performance Tests**

   - Verify no regression in query counts
   - Verify no regression in runtime
   - Check memory usage

4. **Manual Testing**
   - Test optimization with real data
   - Test error scenarios
   - Test concurrent access

---

## 8. Notes

- **Backward Compatibility:** Keep `schedulingService.py` wrapper until all imports updated, then remove
- **Database Migrations:** May need migration for version column in `SchedulingRunModel` (CRIT-4)
- **Configuration:** Consider making magic numbers configurable via `OptimizationConfigModel`
- **Documentation:** Update API documentation after refactors
- **Code Review:** Each PR should be small and focused for easier review

---

**End of Code Review**
