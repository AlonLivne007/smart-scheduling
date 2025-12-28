# US-2: Employee Preferences Implementation Summary

## Overview

This document summarizes the implementation of **US-2: Employee Preferences**, which allows employees to set shift preferences that the optimization algorithm will consider when generating schedules.

## What Was Implemented

### 1. Database Model (`employeePreferencesModel.py`)

Created the `EmployeePreferencesModel` with the following fields:

- **preference_id**: Primary key identifier
- **user_id**: Foreign key to the user (employee) who owns this preference
- **preferred_shift_template_id**: Optional FK to a preferred shift template
- **preferred_day_of_week**: Optional preferred day (enum: MONDAY-SUNDAY)
- **preferred_start_time**: Optional preferred start time
- **preferred_end_time**: Optional preferred end time
- **preference_weight**: Importance weight (0.0-1.0), where higher = more important

**Key Features:**
- Supports multiple types of preferences (shift template, day of week, time range)
- Weight system allows employees to prioritize their preferences
- Cascading deletes ensure data integrity
- Indexed on user_id for efficient queries

### 2. Pydantic Schemas (`employeePreferencesSchema.py`)

Created comprehensive schemas for API validation:

- **EmployeePreferencesCreate**: For creating new preferences
- **EmployeePreferencesUpdate**: For partial updates
- **EmployeePreferencesRead**: For API responses with convenience fields
- **DayOfWeek**: Enum for day of week values

**Validations:**
- Preference weight must be between 0.0 and 1.0
- Time range validation (start < end)
- All fields properly typed and documented

### 3. Controller (`employeePreferencesController.py`)

Implemented business logic with the following functions:

- **create_employee_preference**: Create a new preference with validation
- **get_employee_preferences_by_user**: Get all preferences for a user
- **get_employee_preference**: Get a single preference by ID
- **update_employee_preference**: Update an existing preference
- **delete_employee_preference**: Delete a preference

**Features:**
- Comprehensive validation (user exists, shift template exists, time range valid)
- Proper error handling with meaningful messages
- Authorization checks (employees can only modify their own preferences)
- Serialization helper to convert ORM to Pydantic models

### 4. API Routes (`employeePreferencesRoutes.py`)

Defined RESTful endpoints following the pattern `/employees/{user_id}/preferences`:

**Endpoints:**

1. `POST /employees/{user_id}/preferences` - Create a new preference
2. `GET /employees/{user_id}/preferences` - Get all preferences for a user
3. `GET /employees/{user_id}/preferences/{preference_id}` - Get a single preference
4. `PUT /employees/{user_id}/preferences/{preference_id}` - Update a preference
5. `DELETE /employees/{user_id}/preferences/{preference_id}` - Delete a preference

**Authorization:**
- Employees can only manage their own preferences
- Managers can manage preferences for any employee
- All endpoints require authentication

### 5. Server Integration

Updated `server.py` to:
- Import the new model (`employeePreferencesModel`)
- Import and register the new routes (`employeePreferencesRoutes`)
- Ensure the table is created in the database

## How It Works

### Creating a Preference

An employee can create multiple preferences with different priorities:

```json
POST /employees/5/preferences
{
  "preferred_shift_template_id": 2,
  "preferred_day_of_week": "MONDAY",
  "preference_weight": 0.8
}
```

Or specify a time range preference:

```json
POST /employees/5/preferences
{
  "preferred_start_time": "09:00:00",
  "preferred_end_time": "17:00:00",
  "preference_weight": 0.9
}
```

### Viewing Preferences

```json
GET /employees/5/preferences

Response:
[
  {
    "preference_id": 1,
    "user_id": 5,
    "preferred_shift_template_id": 2,
    "preferred_day_of_week": "MONDAY",
    "preferred_start_time": null,
    "preferred_end_time": null,
    "preference_weight": 0.8,
    "user_full_name": "John Doe",
    "shift_template_name": "Morning Shift"
  }
]
```

### Updating a Preference

```json
PUT /employees/5/preferences/1
{
  "preference_weight": 0.9,
  "preferred_day_of_week": "TUESDAY"
}
```

### Deleting a Preference

```json
DELETE /employees/5/preferences/1
```

## Integration with Optimization

The preferences are stored and ready to be used by the optimization algorithm (US-8). The optimizer will:

1. Query all preferences for eligible employees
2. Use `preference_weight` to scale the preference scores
3. Include preference satisfaction in the objective function
4. Balance preferences against other constraints (coverage, fairness, etc.)

## Database Schema

The `employee_preferences` table was automatically created with:

```sql
CREATE TABLE employee_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    preferred_shift_template_id INTEGER REFERENCES shift_templates(shift_template_id) ON DELETE SET NULL,
    preferred_day_of_week VARCHAR(20),
    preferred_start_time TIME,
    preferred_end_time TIME,
    preference_weight FLOAT NOT NULL DEFAULT 0.5,
    INDEX idx_user_preferences (user_id)
);
```

## Testing the API

You can test the endpoints using:

1. **Swagger UI**: http://localhost:8000/docs
2. **cURL** or **Postman**
3. Frontend integration (when UI is built)

Example with authentication:

```bash
# 1. Login to get token
POST /users/login
{
  "email": "employee@example.com",
  "password": "password123"
}

# 2. Use token to create preference
POST /employees/5/preferences
Headers: Authorization: Bearer <token>
{
  "preferred_shift_template_id": 2,
  "preference_weight": 0.8
}
```

## Files Created/Modified

**Created:**
- `backend/app/db/models/employeePreferencesModel.py` - ORM model
- `backend/app/schemas/employeePreferencesSchema.py` - Pydantic schemas
- `backend/app/api/controllers/employeePreferencesController.py` - Business logic
- `backend/app/api/routes/employeePreferencesRoutes.py` - API endpoints

**Modified:**
- `backend/app/server.py` - Added imports and route registration
- `backend/app/db/models/userModel.py` - Added `preferences` relationship

## Next Steps

This implementation completes US-2. The preferences are now available for:

1. **US-6: MIP Model Builder** - Will read preferences to build preference scores
2. **US-8: MIP Solver Integration** - Will include preferences in the objective function
3. **Frontend UI** - Employees can set their preferences through a user-friendly interface

The preference system is fully functional and ready to improve employee satisfaction in the scheduling optimization!
