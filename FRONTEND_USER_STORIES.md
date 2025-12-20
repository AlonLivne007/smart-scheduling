# Frontend User Stories - Smart Scheduling System

> **Priority Legend:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## 1. NOTIFICATIONS & FEEDBACK SYSTEM 🔴 (Quick Win)

### US-001: Toast Notifications for User Actions
**Priority:** 🔴 Critical  
**Story Points:** 3  
**As a** user  
**I want to** see non-intrusive notifications when I perform actions  
**So that** I receive immediate feedback on success or errors  

**Acceptance Criteria:**
- [ ] Implement toast notification library (e.g., react-hot-toast or sonner)
- [ ] Toast appears for successful operations (create, update, delete)
- [ ] Toast appears for error operations with meaningful error message
- [ ] Toast appears for info messages (e.g., "Loading...")
- [ ] Notifications auto-dismiss after 3-5 seconds
- [ ] Multiple notifications can stack vertically
- [ ] Different color/icon for success (green), error (red), info (blue), warning (yellow)
- [ ] Notifications are dismissible with X button

**Technical Notes:**
- Install: `npm install react-hot-toast`
- Integrate in MainLayout so available across entire app
- Create utility: `lib/notifications.js` with `showSuccess()`, `showError()`, `showInfo()` helpers

---

### US-002: Error Boundary Component
**Priority:** 🔴 Critical  
**Story Points:** 5  
**As a** user  
**I want to** see a helpful error page instead of blank screen on crash  
**So that** I can understand what went wrong and recover  

**Acceptance Criteria:**
- [ ] Error Boundary component created to wrap all pages
- [ ] Displays error message, stack trace (dev only), and error code
- [ ] "Retry" button to reload the page
- [ ] "Go Home" button to navigate back to dashboard
- [ ] Styled consistently with app theme
- [ ] Logs errors to console for debugging
- [ ] Different UI for 404 (Not Found) vs 500 (Server Error)

**Technical Notes:**
- React docs: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
- Create `components/ErrorBoundary.jsx`

---

## 2. LOADING STATES & SKELETONS 🔴 (Quick Win)

### US-003: Loading Skeleton Components
**Priority:** 🔴 Critical  
**Story Points:** 5  
**As a** user  
**I want to** see skeleton loaders while data is loading  
**So that** I perceive the app as responsive and know something is happening  

**Acceptance Criteria:**
- [ ] Create Skeleton component with animated placeholder
- [ ] Skeleton component supports different sizes (small, medium, large)
- [ ] MetricCard shows skeleton state while loading
- [ ] Employee list shows multiple skeleton rows while loading
- [ ] Skeleton animates with pulse effect
- [ ] Skeleton color matches card background (light gray shimmer)
- [ ] When data loads, skeleton smoothly transitions to content

**Technical Notes:**
- Install: `npm install react-loading-skeleton`
- Or create custom skeleton with Tailwind animation
- Use in: HomePage metrics, EmployeesPage list, SchedulePage

---

### US-004: Loading Spinners for Page Transitions
**Priority:** 🟠 High  
**Story Points:** 3  
**As a** user  
**I want to** see a loading spinner when navigating between pages  
**So that** I know a page is loading and not frozen  

**Acceptance Criteria:**
- [ ] Spinner appears when route changes
- [ ] Spinner displays in center of page or in header
- [ ] Spinner disappears when page content loads
- [ ] Spinner styled to match app theme (blue gradient)
- [ ] Optional: Smooth fade in/out of spinner

**Technical Notes:**
- Create `components/LoadingSpinner.jsx` with animated icon
- Use with React Router loading states

---

## 3. DASHBOARD IMPROVEMENTS 🟠 (High Priority)

### US-005: Connect Dashboard Metrics to Backend
**Priority:** 🟠 High  
**Story Points:** 5  
**As a** manager  
**I want to** see real employee and schedule metrics on the dashboard  
**So that** I have an accurate overview of my workforce  

**Acceptance Criteria:**
- [ ] "Total Employees" metric fetches from `GET /users/`
- [ ] "Upcoming Shifts" metric fetches shifts for next 7 days from `GET /planned-shifts/`
- [ ] "Coverage Rate" calculated as: (total assignments / total required assignments) * 100
- [ ] Metrics update with loading skeleton while fetching
- [ ] Error state shows if API calls fail
- [ ] Metrics display with proper formatting (numbers, percentages)
- [ ] Metrics clickable to drill into details (future phase)

**API Calls:**
```
GET /users/ → count results
GET /planned-shifts/ → filter by date range
GET /shift-assignments/ → count for coverage
```

**Technical Notes:**
- Use `useEffect` in HomePage component
- Create `api/metrics.js` with helper functions
- Handle loading/error states with Toast notifications

---

### US-006: Dynamic Recent Activity Feed
**Priority:** 🟡 Medium  
**Story Points:** 8  
**As a** manager  
**I want to** see recent system activity (new users, assignments, approvals)  
**So that** I'm aware of important changes  

**Acceptance Criteria:**
- [ ] Activity feed shows last 5-10 recent actions
- [ ] Activity types: User Created, Shift Assigned, Time-off Approved/Rejected, Schedule Created
- [ ] Each activity shows: Action description, User who performed it, Timestamp
- [ ] Timestamp displays as relative time (e.g., "2 minutes ago")
- [ ] Activities refresh every 30 seconds (or on manual refresh)
- [ ] Icon/color coding by activity type
- [ ] "View All" link to expanded activity page (future)

**Technical Notes:**
- Might require new backend endpoint: `GET /activity-log/` (future feature)
- For now: Mock with static data
- Use library for relative timestamps: `date-fns` (already in deps)

---

### US-007: Weekly Schedule Widget
**Priority:** 🟡 Medium  
**Story Points:** 8  
**As a** manager  
**I want to** see upcoming week's schedule at a glance on the dashboard  
**So that** I can quickly check coverage for the next 7 days  

**Acceptance Criteria:**
- [ ] Widget displays Mon-Sun of next week
- [ ] Shows count of planned shifts per day
- [ ] Shows count of assigned vs. unassigned for each day
- [ ] Days with gaps highlighted in different color
- [ ] Clicking a day navigates to Schedule page filtered for that day
- [ ] Responsive on mobile (scrollable if needed)
- [ ] Shows total shifts and coverage % for the week

**API Calls:**
```
GET /planned-shifts/ filtered by next 7 days
GET /shift-assignments/ to count assignments
```

---

## 4. FORMS & INPUT VALIDATION 🟠 (High Priority)

### US-008: Enhanced InputField Validation
**Priority:** 🟠 High  
**Story Points:** 5  
**As a** user  
**I want to** see real-time validation feedback on form fields  
**So that** I can fix errors before submitting  

**Acceptance Criteria:**
- [x] InputField component shows validation errors in red text below field
- [x] Error appears after field is touched/blurred
- [x] Error clears when user starts typing correct value
- [x] Visual indicator (red border) on invalid field
- [x] Success state (green border) on valid field
- [x] Support for common validations: email, min/max length, required, pattern
- [x] Custom validation rules can be passed as props
- [x] Disabled state for read-only fields

**Technical Notes:**
- Update `components/ui/InputField.jsx`
- Can use Zod or Yup for schema validation

**✅ IMPLEMENTED:**
- Enhanced InputField component with comprehensive validation
- Built-in validators: email, minLength, maxLength, pattern, number, min, max, required
- Visual states: error (red), success (green), disabled, readonly
- Touch/blur validation behavior
- Icon indicators (checkmark/error)
- Helper text support
- Demo page: `/debug/input-validation`

---

### US-009: Form Submission Confirmation Dialogs
**Priority:** 🟡 Medium  
**Story Points:** 3  
**As a** user  
**I want to** see confirmation before deleting or making critical changes  
**So that** I don't accidentally delete important data  

**Acceptance Criteria:**
- [x] Modal appears before delete operations
- [x] Modal shows what will be deleted
- [x] "Cancel" and "Confirm Delete" buttons
- [x] Confirmation required for: Delete user, Delete schedule, Remove assignment
- [x] Optional: Show side effects (e.g., "This will also delete 5 planned shifts")
- [x] Styled consistently with app theme

**Technical Notes:**
- Create `components/ConfirmDialog.jsx` component
- Update existing Modal component

**✅ IMPLEMENTED:**
- ConfirmDialog component with full feature set
- Default and danger variants with color coding
- Side effects display for cascade delete warnings
- Keyboard shortcuts (Esc, Enter) for quick actions
- Loading state support for async operations
- Focus management and accessibility (ARIA)
- Custom icon support per dialog
- Backdrop click to dismiss
- Prevents background scroll when open
- Demo page: `/debug/confirm-dialog`

---

## 5. EMPLOYEE/USER MANAGEMENT 🟠 (High Priority)

### US-010: Employee Directory with Search & Filters
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** view all employees with search and filter capabilities  
**So that** I can quickly find employees by name or role  

**Acceptance Criteria:**
- [ ] List displays all employees from `GET /users/`
- [ ] Search box filters by name/email in real-time
- [ ] Filter dropdown by role
- [ ] Sort options: Name (A-Z, Z-A), Joined (newest, oldest)
- [ ] Column headers clickable to sort
- [ ] Pagination (10 employees per page)
- [ ] Each employee row shows: Name, Email, Roles, Manager status
- [ ] Click employee row to view detail page
- [ ] Edit and Delete buttons for each row (manager only)

**API Calls:**
```
GET /users/ → all employees
GET /roles/ → for filter dropdown
```

**Technical Notes:**
- Create new page: `pages/Admin/Employees/EmployeeDirectoryPage.jsx` or extend existing
- Use `Array.filter()` and `Array.sort()` for client-side search/sort initially
- Can move to backend filtering later

---

### US-011: Employee Profile / Detail View
**Priority:** 🟡 Medium  
**Story Points:** 5  
**As a** manager  
**I want to** view detailed employee profile including assignments and time-off  
**So that** I can see the full picture of an employee's schedule and status  

**Acceptance Criteria:**
- [ ] Profile shows: Name, Email, Roles, Manager status
- [ ] Displays assigned shifts for current week
- [ ] Shows pending time-off requests
- [ ] Shows approved time-off periods
- [ ] Edit button to modify employee info
- [ ] Navigation back to employee list
- [ ] Responsive layout

**API Calls:**
```
GET /users/{user_id} → employee details
GET /shift-assignments/by-user/{user_id} → their assignments
GET /time-off/requests/ filtered by user_id → their time-off
```

---

### US-012: Add/Edit User Form with Validation
**Priority:** 🟡 Medium  
**Story Points:** 5  
**As a** manager  
**I want to** create and edit employee records with form validation  
**So that** I maintain data quality and avoid duplicate emails  

**Acceptance Criteria:**
- [ ] Form fields: Full name, Email, Password (create only), Roles (multi-select), Manager checkbox
- [ ] Email validated as unique (check with backend)
- [ ] Password required on create, optional on edit
- [ ] Roles shown as multi-select checkboxes
- [ ] Form validation before submit (all required fields filled, email valid)
- [ ] Success toast on save
- [ ] Error handling with field-level errors
- [ ] Cancel button to discard changes

**API Calls:**
```
POST /users/ → create
PUT /users/{user_id} → update
GET /roles/ → for role selection
```

---

## 6. TIME-OFF MANAGEMENT 🟠 (High Priority)

### US-013: Employee Time-Off Request Form
**Priority:** 🟠 High  
**Story Points:** 5  
**As an** employee  
**I want to** request time off through a form  
**So that** managers know when I'm unavailable  

**Acceptance Criteria:**
- [ ] Form fields: Start date, End date, Request type (Vacation/Sick/Personal/Other)
- [ ] Date range picker (can use existing input or library)
- [ ] Type dropdown with 4 options
- [ ] Submit button creates request via `POST /time-off/requests/`
- [ ] Success message shows request submitted
- [ ] Form clears or redirects after successful submission
- [ ] Validation: start_date before end_date, dates in future
- [ ] Cancel button

**API Calls:**
```
POST /time-off/requests/ → create request (auto uses current user)
```

---

### US-014: Time-Off Requests Management Page (Manager View)
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** view, approve, and reject employee time-off requests  
**So that** I can manage workforce availability  

**Acceptance Criteria:**
- [ ] Table/list of all time-off requests
- [ ] Columns: Employee name, Type, Start date, End date, Status (PENDING/APPROVED/REJECTED), Actions
- [ ] Filter by status: All, Pending, Approved, Rejected
- [ ] Filter by request type
- [ ] Sort by date, name, status
- [ ] Each pending request has "Approve" and "Reject" buttons
- [ ] Approved/Rejected requests show approver name and date
- [ ] Approve/Reject triggers API call with toast feedback
- [ ] Approved requests show in employee profiles

**API Calls:**
```
GET /time-off/requests/ → all requests
POST /time-off/requests/{request_id}/approve → approve
POST /time-off/requests/{request_id}/reject → reject
```

---

### US-015: Employee Time-Off History
**Priority:** 🟡 Medium  
**Story Points:** 5  
**As an** employee  
**I want to** view my time-off requests and their status  
**So that** I know which requests are approved and upcoming  

**Acceptance Criteria:**
- [ ] Shows all my time-off requests (current user only)
- [ ] Columns: Type, Start date, End date, Status, Submitted date
- [ ] Filter by status: Pending, Approved, Rejected
- [ ] Edit/Delete buttons for PENDING requests only
- [ ] Approved requests show approver and approval date
- [ ] Rejected requests show reason (if available)
- [ ] Option to create new request via button

**API Calls:**
```
GET /time-off/requests/ → filtered to show only current user's
```

---

## 7. SCHEDULE MANAGEMENT 🟠 (High Priority)

### US-016: Schedule Page - List View
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** view all weekly schedules in a list  
**So that** I can select and manage existing schedules or create new ones  

**Acceptance Criteria:**
- [ ] List of all weekly schedules from `GET /weekly-schedules/`
- [ ] Columns: Week starting (date), Created by, Number of shifts, Coverage status
- [ ] Sort by date (newest, oldest)
- [ ] Create New Schedule button
- [ ] Click row to view schedule detail
- [ ] Edit and Delete buttons for each schedule
- [ ] Pagination if more than 10 schedules

**API Calls:**
```
GET /weekly-schedules/ → all schedules
```

---

### US-017: Create Weekly Schedule Wizard
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** create a new weekly schedule through a step-by-step wizard  
**So that** I can set up shifts for the coming week  

**Acceptance Criteria:**
- [ ] Step 1: Select week start date (date picker)
- [ ] Step 2: Choose which shift templates to use (multi-select checkboxes)
- [ ] Step 3: Set which days of week to create shifts (Mon-Sun checkboxes)
- [ ] Step 4: Review and confirm
- [ ] Form validation: week date selected, at least 1 template, at least 1 day
- [ ] Submit creates WeeklySchedule and all PlannedShifts
- [ ] Success message with link to view new schedule
- [ ] Cancel button to go back

**API Calls:**
```
POST /weekly-schedules/ → create schedule
POST /planned-shifts/ → create shifts for selected days/templates
GET /shift-templates/ → for template selection
```

---

### US-018: Schedule Detail - Calendar View
**Priority:** 🟠 High  
**Story Points:** 13  
**As a** manager  
**I want to** view a weekly schedule in calendar format  
**So that** I can see shifts visually and manage assignments  

**Acceptance Criteria:**
- [ ] Calendar shows one week (Mon-Sun)
- [ ] Each day shows all planned shifts for that day
- [ ] Each shift card shows: Template name, Time, Location, Assignment count/status
- [ ] Shift card color indicates status: Green (fully assigned), Yellow (partial), Red (unassigned)
- [ ] Click shift to view/edit assignments
- [ ] Drag-and-drop to reassign employee (future phase)
- [ ] Button to edit shift details
- [ ] Button to delete shift
- [ ] Navigation arrows to view previous/next week

**API Calls:**
```
GET /weekly-schedules/{schedule_id} → full schedule with shifts
```

**Technical Notes:**
- Library: `react-calendar` or `@fullcalendar/react`
- Or build custom calendar with Tailwind

---

### US-019: Shift Assignment Management
**Priority:** 🟠 High  
**Story Points:** 8  
**As a** manager  
**I want to** assign employees to shifts from a detail view  
**So that** I can fill positions and track coverage  

**Acceptance Criteria:**
- [ ] Modal/side panel shows shift details and list of current assignments
- [ ] Add Assignment button opens form to add employee
- [ ] Form shows: Employee dropdown, Role dropdown (filtered by shift's required roles)
- [ ] Validation: Employee and Role selected, no duplicate employee per shift
- [ ] Submit creates assignment via `POST /shift-assignments/`
- [ ] Success message and assignment appears in list
- [ ] Delete button removes each assignment with confirmation
- [ ] Unassigned roles highlighted
- [ ] Shift status updates automatically based on assignments

**API Calls:**
```
GET /planned-shifts/{shift_id} → shift details with assignments
POST /shift-assignments/ → add assignment
DELETE /shift-assignments/{assignment_id} → remove assignment
GET /users/ → for employee selection
GET /roles/ → for role selection (could filter by shift's required_roles)
```

---

## 8. SYSTEM SETTINGS 🟡 (Medium Priority)

### US-020: System Constraints Configuration Page
**Priority:** 🟡 Medium  
**Story Points:** 8  
**As a** manager  
**I want to** configure global work constraints (max hours, rest periods, etc.)  
**So that** I enforce company policies during scheduling  

**Acceptance Criteria:**
- [ ] Table showing all system constraints
- [ ] Columns: Constraint name, Current value, Is hard constraint (toggle)
- [ ] Edit button or inline edit to change values
- [ ] Constraints displayed: Max hours/week, Min hours/week, Max consecutive days, Min rest hours, Max shifts/week
- [ ] Validation: Values must be positive numbers
- [ ] Save changes via `PUT /system-constraints/{id}`
- [ ] Success toast on save
- [ ] Description/tooltip for each constraint explaining its purpose
- [ ] Hard constraint toggle (can be soft/preferred)

**API Calls:**
```
GET /system-constraints/ → all constraints
PUT /system-constraints/{constraint_id} → update constraint
```

---

### US-021: Company Settings Form
**Priority:** 🟡 Medium  
**Story Points:** 5  
**As a** manager  
**I want to** configure company information and preferences  
**So that** the system reflects our organization's details  

**Acceptance Criteria:**
- [ ] Form fields: Company name, Industry, Address, Phone
- [ ] Fields can be edited and saved
- [ ] Success message on save
- [ ] Backend storage (requires new endpoint)
- [ ] Form pre-populated with saved values

**Technical Notes:**
- Requires backend endpoint (future: `GET/PUT /company-settings/`)
- For now: Mock or make read-only display

---

## 9. ACCESSIBILITY & RESPONSIVE DESIGN 🟢 (Low Priority - Ongoing)

### US-022: Mobile Responsive Design
**Priority:** 🟢 Low  
**Story Points:** 13  
**As a** mobile user  
**I want to** use the scheduling app on my phone  
**So that** I can manage schedules on-the-go  

**Acceptance Criteria:**
- [ ] All pages tested on mobile (375px width)
- [ ] Sidebar collapses to hamburger menu on mobile
- [ ] Tables convert to card layout on mobile
- [ ] Forms stack vertically
- [ ] Calendar possibly switches to day/list view on mobile
- [ ] Touch-friendly button sizes (min 44px)
- [ ] No horizontal scrolling on mobile
- [ ] Navigation remains accessible

**Technical Notes:**
- Tailwind breakpoints: `sm: 640px`, `md: 768px`, `lg: 1024px`
- Test with Chrome DevTools mobile view

---

### US-023: Dark Mode Toggle
**Priority:** 🟢 Low  
**Story Points:** 8  
**As a** user  
**I want to** switch between light and dark themes  
**So that** I can reduce eye strain in low-light environments  

**Acceptance Criteria:**
- [ ] Toggle button in navbar or settings
- [ ] Dark theme colors defined and applied throughout
- [ ] User preference saved to localStorage
- [ ] Preference persists across sessions
- [ ] All components tested in dark mode
- [ ] Charts/metrics remain readable in dark mode

**Technical Notes:**
- Use Tailwind `dark:` prefix
- Store preference in localStorage as `theme: 'light'|'dark'`
- Initialize on app load from localStorage

---

### US-024: Keyboard Navigation & ARIA Labels
**Priority:** 🟢 Low  
**Story Points:** 13  
**As a** keyboard user  
**I want to** navigate the app using only keyboard  
**So that** I can use the app without a mouse  

**Acceptance Criteria:**
- [ ] All buttons, links, inputs are keyboard accessible (Tab order)
- [ ] Focus indicators visible on all interactive elements
- [ ] ARIA labels on buttons without text labels
- [ ] Form labels associated with inputs
- [ ] Modals trap focus and have close button
- [ ] Tables have proper header markup
- [ ] Screen reader test: Can navigate and use all features

**Technical Notes:**
- Use semantic HTML: `<button>`, `<a>`, `<form>`, `<label>`
- Add `tabIndex` where needed
- Use `aria-label`, `aria-describedby`, `role` attributes
- Test with screen reader (NVDA on Windows, JAWS, VoiceOver on Mac)

---

## 10. ADVANCED FEATURES 🟢 (Future/Low Priority)

### US-025: Shift Template Management UI
**Priority:** 🟢 Low  
**Story Points:** 8  
**As a** manager  
**I want to** create and manage shift templates through the UI  
**So that** I can quickly reuse common shift patterns  

**Acceptance Criteria:**
- [ ] List of all shift templates
- [ ] Create new template form: Name, Start time, End time, Location, Required roles (multi-select)
- [ ] Edit existing template
- [ ] Delete template (with confirmation)
- [ ] Validation: Template name unique, times valid

**API Calls:**
```
GET /shift-templates/
POST /shift-templates/
PUT /shift-templates/{template_id}
DELETE /shift-templates/{template_id}
GET /roles/ → for role selection
```

---

### US-026: Role Management UI
**Priority:** 🟢 Low  
**Story Points:** 5  
**As a** manager  
**I want to** create and manage roles through the UI  
**So that** I can define job positions for the company  

**Acceptance Criteria:**
- [ ] List of all roles
- [ ] Create new role form: Role name (unique)
- [ ] Edit role name
- [ ] Delete role (with confirmation)
- [ ] Delete prevented if role is in use

**API Calls:**
```
GET /roles/
POST /roles/
PUT /roles/{role_id}
DELETE /roles/{role_id}
```

---

### US-027: Export Schedule to PDF/CSV
**Priority:** 🟢 Low  
**Story Points:** 8  
**As a** manager  
**I want to** export schedules to PDF or CSV  
**So that** I can share schedules via email or print them  

**Acceptance Criteria:**
- [ ] Export button on schedule detail page
- [ ] Option to export as PDF or CSV
- [ ] PDF: Nice formatted calendar view with shift assignments
- [ ] CSV: Spreadsheet with columns: Date, Time, Location, Employee, Role
- [ ] File downloads with sensible filename (e.g., `schedule_week_2025-01-15.pdf`)

**Technical Notes:**
- Libraries: `react-pdf`, `csv-export-js` or similar
- Or use server-side PDF generation

---

### US-028: Scheduling Optimization (Phase 2)
**Priority:** 🟢 Low (Future Phase)  
**Story Points:** 21  
**As a** manager  
**I want to** run automated optimization to assign shifts optimally  
**So that** I minimize conflicts and balance workload fairly  

**Acceptance Criteria:**
- [ ] "Run Optimization" button on schedule detail
- [ ] Modal appears showing optimization parameters (fairness weight, preference weight)
- [ ] Loading spinner while optimization runs
- [ ] Optimization results displayed with proposed assignments
- [ ] "Preview" to see proposed assignments before applying
- [ ] "Apply" button to accept all proposed assignments
- [ ] "Reject" to discard and keep manual assignments

**API Calls (Future):**
```
POST /optimization/run/ → start optimization
GET /optimization/results/{run_id} → get results
POST /optimization/apply/{run_id} → apply solutions
```

---

## Implementation Roadmap

### **Phase 1: Foundation (Weeks 1-2)** 🔴
Priority: Critical features for baseline functionality
- US-001: Toast Notifications
- US-002: Error Boundary
- US-003: Loading Skeletons
- US-004: Loading Spinners
- US-008: Input Validation
- US-009: Confirmation Dialogs

### **Phase 2: Dashboard (Week 2)** 🔴
- US-005: Connect Dashboard Metrics
- US-006: Recent Activity Feed
- US-007: Weekly Schedule Widget

### **Phase 3: Employee Management (Week 3)** 🟠
- US-010: Employee Directory
- US-011: Employee Profile
- US-012: Add/Edit User Form

### **Phase 4: Time-Off (Week 3-4)** 🟠
- US-013: Time-Off Request Form
- US-014: Manager Time-Off Management
- US-015: Employee Time-Off History

### **Phase 5: Schedule Management (Week 4-5)** 🟠
- US-016: Schedule List View
- US-017: Create Schedule Wizard
- US-018: Calendar View
- US-019: Shift Assignment Management

### **Phase 6: Settings & Polish (Week 5)** 🟡
- US-020: System Constraints
- US-021: Company Settings
- US-022: Mobile Responsive (ongoing)
- US-023: Dark Mode (optional)

### **Phase 7: Advanced (Future)** 🟢
- US-024: Accessibility
- US-025: Shift Template UI
- US-026: Role Management UI
- US-027: Export
- US-028: Optimization (Phase 2 backend feature)

---

## Development Priority Matrix

```
HIGH IMPACT + QUICK WIN:
✅ US-001 Toast Notifications (3 pts)
✅ US-002 Error Boundary (5 pts)
✅ US-003 Loading Skeletons (5 pts)
✅ US-004 Loading Spinners (3 pts)

HIGH IMPACT + MODERATE EFFORT:
✅ US-005 Dashboard Metrics (5 pts)
✅ US-008 Input Validation (5 pts)
✅ US-010 Employee Directory (8 pts)
✅ US-013 Time-Off Form (5 pts)
✅ US-014 Time-Off Manager (8 pts)
✅ US-016 Schedule List (8 pts)
✅ US-018 Calendar View (13 pts)
✅ US-019 Shift Assignment (8 pts)

NICE-TO-HAVE:
⭐ US-006 Activity Feed (8 pts)
⭐ US-007 Weekly Widget (8 pts)
⭐ US-009 Confirmation Dialogs (3 pts)
⭐ US-020 System Constraints (8 pts)
⭐ US-022 Responsive Design (13 pts)
```

**Total Story Points (Critical Path):** ~85 points
**Estimated Timeline:** 4-5 weeks for one developer

---

## Notes

- All user stories assume JWT authentication is working (backend ready)
- API endpoints referenced are documented in `BACKEND_FRONTEND_INTEGRATION_GUIDE.md`
- Each story should have unit tests and component tests
- UI should be responsive (mobile-first approach)
- Dark mode considerations for later iterations
