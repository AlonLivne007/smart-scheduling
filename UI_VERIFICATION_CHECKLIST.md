# UI Verification Checklist - Service Layer Fixes

This checklist helps you verify that all the critical and high-priority fixes are working correctly through the UI.

## 🎯 Where to Test

**Primary Location:** Schedule Page → Select a Weekly Schedule → Optimization Panel

**Navigation Path:**

1. Go to **Admin** → **Schedules** (or **Schedule Page**)
2. Select an existing weekly schedule
3. Look for the **"Schedule Optimization"** panel

---

## ✅ Verification Checklist

### 1. **Optimization Run Status Updates** (CRIT-4: Race Condition Protection)

**What to Check:**

- [ ] Click **"Run Optimization"** button
- [ ] Status should immediately show **"PENDING"** or **"RUNNING"**
- [ ] Status should update automatically every 3 seconds (polling)
- [ ] Status should transition: `PENDING` → `RUNNING` → `COMPLETED` or `FAILED`
- [ ] **No duplicate runs** should be created if you click the button multiple times quickly

**Expected Behavior:**

- Status updates smoothly without flickering
- Only one run is created per button click
- Status badge shows correct color (blue for RUNNING, green for COMPLETED, red for FAILED)

---

### 2. **Error Messages Display** (CRIT-3: Error Handling)

**What to Check:**

- [ ] If optimization fails, you should see:
  - [ ] **Red error banner** with error message
  - [ ] **Solver Status** badge (INFEASIBLE, ERROR, etc.)
  - [ ] **Error message text** explaining what went wrong
  - [ ] **Runtime** displayed even on failure

**Test Scenarios:**

1. **Infeasible Solution:**

   - Create a schedule with impossible constraints (e.g., 100 max hours per week, only 1 employee)
   - Run optimization
   - Should see: "INFEASIBLE" status with error message

2. **Validation Failure:**
   - If solution violates HARD constraints, should see: "HARD constraint violations detected: [details]"

**Expected Error Display:**

```
┌─────────────────────────────────────────┐
│ ❌ Optimization Failed                  │
│                                         │
│ Solver Status: [INFEASIBLE]            │
│ Error: [Detailed error message]        │
│ Runtime: X.XXs                          │
└─────────────────────────────────────────┘
```

---

### 3. **Successful Optimization** (All Fixes Working Together)

**What to Check:**

- [ ] Run optimization on a valid schedule
- [ ] Status should show **"COMPLETED"** (green badge)
- [ ] Results panel should display:
  - [ ] **Total Assignments** count
  - [ ] **Employees Assigned** count
  - [ ] **Runtime** in seconds
  - [ ] **Solver Status** (OPTIMAL or FEASIBLE)
- [ ] **"Apply Solution to Schedule"** button should be visible and clickable

**Expected Success Display:**

```
┌─────────────────────────────────────────┐
│ ✅ Optimization Results                  │
│                                         │
│ Total Assignments: 45                   │
│ Employees Assigned: 12                 │
│ Runtime: 3.45s                          │
│ Status: OPTIMAL                         │
│                                         │
│ [Apply Solution to Schedule]           │
└─────────────────────────────────────────┘
```

---

### 4. **Transaction Safety** (CRIT-2: Transaction Management)

**What to Check:**

- [ ] Click **"Apply Solution to Schedule"**
- [ ] Assignments should be created **atomically** (all or nothing)
- [ ] If an error occurs during apply:
  - [ ] No partial assignments should remain
  - [ ] Error message should be displayed
  - [ ] Schedule should remain in previous state

**Test Scenario:**

1. Apply a solution
2. If it succeeds, all assignments should appear in the schedule
3. If it fails (e.g., conflict), no partial changes should be visible

---

### 5. **Optimization History** (Status Tracking)

**What to Check:**

- [ ] **Optimization History** section shows all previous runs
- [ ] Each run displays:
  - [ ] **Run ID** (#123)
  - [ ] **Status badge** with correct color
  - [ ] **Start time** (formatted date/time)
  - [ ] **Runtime** (if completed)
  - [ ] **Assignment count** (if completed)
- [ ] Clicking a run shows its details
- [ ] Failed runs show error information

**Expected History Display:**

```
Optimization History
┌─────────────────────────────────────────┐
│ ✅ Run #5                               │
│    COMPLETED • 12/15/2024 2:30 PM      │
│    • 3.45s • 45 assignments            │
├─────────────────────────────────────────┤
│ ❌ Run #4                               │
│    FAILED • 12/15/2024 2:25 PM         │
│    • INFEASIBLE                         │
└─────────────────────────────────────────┘
```

---

### 6. **Real-time Status Updates** (Polling)

**What to Check:**

- [ ] Start an optimization
- [ ] Status should update automatically without page refresh
- [ ] Watch the status change from `PENDING` → `RUNNING` → `COMPLETED`
- [ ] Loading spinner should appear during `RUNNING` status
- [ ] Polling should stop once status is `COMPLETED` or `FAILED`

**Expected Behavior:**

- Status updates every 3 seconds automatically
- No need to manually refresh the page
- Smooth transitions between states

---

### 7. **Error Message Quality** (CRIT-3: Improved Error Handling)

**What to Check:**

- [ ] Error messages should be **user-friendly** and **actionable**
- [ ] Technical errors should include context
- [ ] Validation errors should list specific violations

**Good Error Messages:**

- ✅ "HARD constraint violations detected: Employee John has only 8 hours rest between shifts (minimum: 10)"
- ✅ "No feasible solution exists. Please review constraints."
- ✅ "Optimization failed: No eligible employees found"

**Bad Error Messages (should NOT appear):**

- ❌ "Exception: NoneType has no attribute 'x'"
- ❌ "Error 500"
- ❌ Generic "Something went wrong"

---

### 8. **Performance Indicators**

**What to Check:**

- [ ] Runtime should be displayed for completed runs
- [ ] Runtime should be reasonable (typically < 30 seconds for small schedules)
- [ ] Status updates should be responsive (no lag)

**Expected:**

- Runtime shown in seconds (e.g., "3.45s")
- Updates happen within 3 seconds
- No noticeable delays

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path

1. Create a weekly schedule with shifts
2. Add employees with appropriate roles
3. Set reasonable constraints
4. Run optimization
5. **Verify:** Status shows COMPLETED, results displayed, can apply solution

### Scenario 2: Infeasible Constraints

1. Set impossible constraints (e.g., max 1 hour per week, need 100 hours)
2. Run optimization
3. **Verify:** Status shows FAILED with INFEASIBLE, error message explains issue

### Scenario 3: Concurrent Runs (Race Condition Test)

1. Open optimization panel in two browser tabs
2. Click "Run Optimization" in both tabs quickly
3. **Verify:** Only one run is created, no duplicate runs

### Scenario 4: Apply Solution

1. Complete an optimization successfully
2. Click "Apply Solution to Schedule"
3. **Verify:** All assignments appear in schedule, no partial updates

---

## 🚨 Red Flags (Things That Should NOT Happen)

- ❌ Status stuck on "RUNNING" forever
- ❌ Multiple runs created from single button click
- ❌ Partial assignments after failed apply
- ❌ Generic error messages without context
- ❌ Status not updating automatically
- ❌ Page refresh required to see status changes
- ❌ Duplicate error messages
- ❌ Crashes or blank screens

---

## 📊 Summary Dashboard

After testing, you should see:

| Feature                   | Status | Notes                          |
| ------------------------- | ------ | ------------------------------ |
| Status Updates            | ✅     | Updates automatically every 3s |
| Error Messages            | ✅     | Clear, actionable messages     |
| Transaction Safety        | ✅     | All-or-nothing updates         |
| Race Condition Protection | ✅     | No duplicate runs              |
| History Display           | ✅     | All runs visible with details  |
| Apply Solution            | ✅     | Works correctly                |
| Performance               | ✅     | Reasonable runtime             |

---

## 🔍 Additional Verification

### Backend Logs (Optional)

If you have access to backend logs, check for:

- ✅ Proper logging with context (run_id, schedule_id)
- ✅ No duplicate transaction commits
- ✅ Proper error logging with stack traces
- ✅ No print() statements (should use logger)

### Database (Optional)

Check database directly:

- ✅ Only one run record per optimization
- ✅ Run status transitions correctly
- ✅ No orphaned solution records
- ✅ Assignments created atomically

---

## 📝 Notes

- All fixes are **backend-only** - UI should work the same but be more reliable
- Error messages should be more informative
- Status updates should be more consistent
- No new UI features were added, only reliability improvements

---

**Last Updated:** After service layer refactoring
**Tested By:** [Your Name]
**Date:** [Date]
