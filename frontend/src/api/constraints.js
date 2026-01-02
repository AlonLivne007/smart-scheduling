/**
 * System Constraints API Helpers
 * 
 * Functions to manage system-wide work rules and constraints.
 * 
 * @module api/constraints
 */

import api from '../lib/axios.js';

/**
 * Get all system constraints
 * 
 * @returns {Promise<Array>} Array of constraint objects
 * @throws {Error} If API call fails
 */
export const getAllConstraints = async () => {
  const response = await api.get('/system/constraints/');
  return response.data;
};

/**
 * Get a single constraint by ID
 * 
 * @param {number} constraintId - ID of the constraint
 * @returns {Promise<Object>} Constraint object
 * @throws {Error} If API call fails
 */
export const getConstraint = async (constraintId) => {
  const response = await api.get(`/system/constraints/${constraintId}`);
  return response.data;
};

/**
 * Create a new system constraint
 * 
 * @param {Object} constraintData - Constraint data
 * @param {string} constraintData.constraint_type - Type of constraint (MAX_HOURS_PER_WEEK, MIN_HOURS_PER_WEEK, etc.)
 * @param {number} constraintData.constraint_value - Numeric value for the constraint
 * @param {boolean} constraintData.is_hard_constraint - True if must be satisfied, false if soft
 * @returns {Promise<Object>} Created constraint object
 * @throws {Error} If API call fails
 */
export const createConstraint = async (constraintData) => {
  const response = await api.post('/system/constraints/', constraintData);
  return response.data;
};

/**
 * Update an existing constraint
 * 
 * @param {number} constraintId - ID of the constraint to update
 * @param {Object} constraintData - Updated constraint data
 * @returns {Promise<Object>} Updated constraint object
 * @throws {Error} If API call fails
 */
export const updateConstraint = async (constraintId, constraintData) => {
  const response = await api.put(`/system/constraints/${constraintId}`, constraintData);
  return response.data;
};

/**
 * Delete a constraint
 * 
 * @param {number} constraintId - ID of the constraint to delete
 * @returns {Promise<Object>} Success message
 * @throws {Error} If API call fails
 */
export const deleteConstraint = async (constraintId) => {
  const response = await api.delete(`/system/constraints/${constraintId}`);
  return response.data;
};

/**
 * Constraint types available in the system
 */
export const CONSTRAINT_TYPES = {
  MAX_HOURS_PER_WEEK: {
    value: 'MAX_HOURS_PER_WEEK',
    label: 'Maximum Hours Per Week',
    description: 'Maximum allowed working hours in a week',
    unit: 'hours'
  },
  MIN_HOURS_PER_WEEK: {
    value: 'MIN_HOURS_PER_WEEK',
    label: 'Minimum Hours Per Week',
    description: 'Minimum target working hours in a week',
    unit: 'hours'
  },
  MAX_CONSECUTIVE_DAYS: {
    value: 'MAX_CONSECUTIVE_DAYS',
    label: 'Maximum Consecutive Working Days',
    description: 'Maximum days an employee can work consecutively',
    unit: 'days'
  },
  MIN_REST_HOURS: {
    value: 'MIN_REST_HOURS',
    label: 'Minimum Rest Hours',
    description: 'Minimum hours required between shifts',
    unit: 'hours'
  },
  MAX_SHIFTS_PER_WEEK: {
    value: 'MAX_SHIFTS_PER_WEEK',
    label: 'Maximum Shifts Per Week',
    description: 'Maximum number of shifts in a week',
    unit: 'shifts'
  },
  MIN_SHIFTS_PER_WEEK: {
    value: 'MIN_SHIFTS_PER_WEEK',
    label: 'Minimum Shifts Per Week',
    description: 'Minimum number of shifts in a week',
    unit: 'shifts'
  }
};
