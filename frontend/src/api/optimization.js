/**
 * Optimization API Helpers
 * 
 * Functions to manage scheduling optimization runs and solutions.
 * 
 * @module api/optimization
 */

import api from '../lib/axios.js';

/**
 * Trigger optimization for a weekly schedule
 * 
 * @param {number} weeklyScheduleId - ID of the weekly schedule to optimize
 * @param {number|null} configId - Optional optimization config ID (uses default if null)
 * @returns {Promise<Object>} Optimization run object
 * @throws {Error} If API call fails
 */
export const triggerOptimization = async (weeklyScheduleId, configId = null) => {
  const url = `/scheduling/optimize`;
  const params = { weekly_schedule_id: weeklyScheduleId };
  if (configId) params.config_id = configId;
  
  const response = await api.post(url, null, { params });
  return response.data;
};

/**
 * Get all scheduling runs
 * 
 * @param {Object} filters - Optional filters
 * @param {number} filters.weekly_schedule_id - Filter by schedule ID
 * @param {string} filters.status - Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
 * @returns {Promise<Array>} Array of scheduling run objects
 * @throws {Error} If API call fails
 */
export const getAllRuns = async (filters = {}) => {
  const response = await api.get('/scheduling-runs/', { params: filters });
  return response.data;
};

/**
 * Get a single scheduling run by ID
 * 
 * @param {number} runId - ID of the scheduling run
 * @returns {Promise<Object>} Scheduling run object
 * @throws {Error} If API call fails
 */
export const getRun = async (runId) => {
  const response = await api.get(`/scheduling-runs/${runId}`);
  return response.data;
};

/**
 * Get solutions for a scheduling run
 * 
 * @param {number} runId - ID of the scheduling run
 * @returns {Promise<Array>} Array of solution objects
 * @throws {Error} If API call fails
 */
export const getSolutions = async (runId) => {
  const response = await api.get(`/scheduling-runs/${runId}/solutions`);
  return response.data;
};

/**
 * Apply a scheduling solution to create actual shift assignments
 * 
 * @param {number} runId - ID of the scheduling run
 * @param {boolean} overwrite - Whether to overwrite existing assignments
 * @returns {Promise<Object>} Result object with assignments_created, shifts_updated, message
 * @throws {Error} If API call fails
 */
export const applySolution = async (runId, overwrite = false) => {
  const response = await api.post(`/scheduling-runs/${runId}/apply`, null, {
    params: { overwrite }
  });
  return response.data;
};

/**
 * Delete a scheduling run
 * 
 * @param {number} runId - ID of the scheduling run
 * @returns {Promise<Object>} Success message
 * @throws {Error} If API call fails
 */
export const deleteRun = async (runId) => {
  const response = await api.delete(`/scheduling-runs/${runId}`);
  return response.data;
};
