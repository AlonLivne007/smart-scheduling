import apiClient from '../lib/axios';

/**
 * Time-Off Request API
 */

/**
 * Get all time-off requests (optionally filtered)
 * @param {Object} filters - Optional filters (user_id, status)
 * @returns {Promise<Array>} List of time-off requests
 */
export async function fetchTimeOffRequests(filters = {}) {
  const params = new URLSearchParams();
  if (filters.user_id) params.append('user_id', filters.user_id);
  if (filters.status) params.append('status', filters.status);
  
  const response = await apiClient.get(`/time-off/requests/?${params.toString()}`);
  return response.data;
}

/**
 * Get a single time-off request by ID
 * @param {number} requestId - Request ID
 * @returns {Promise<Object>} Time-off request details
 */
export async function fetchTimeOffRequestById(requestId) {
  const response = await apiClient.get(`/time-off/requests/${requestId}`);
  return response.data;
}

/**
 * Create a new time-off request
 * @param {Object} requestData - Request data
 * @param {string} requestData.start_date - Start date (YYYY-MM-DD)
 * @param {string} requestData.end_date - End date (YYYY-MM-DD)
 * @param {string} requestData.request_type - Type (VACATION, SICK, PERSONAL, OTHER)
 * @returns {Promise<Object>} Created request
 */
export async function createTimeOffRequest(requestData) {
  const response = await apiClient.post('/time-off/requests/', requestData);
  return response.data;
}

/**
 * Approve a time-off request (Manager only)
 * @param {number} requestId - Request ID
 * @returns {Promise<Object>} Updated request
 */
export async function approveTimeOffRequest(requestId) {
  const response = await apiClient.post(`/time-off/requests/${requestId}/approve`);
  return response.data;
}

/**
 * Reject a time-off request (Manager only)
 * @param {number} requestId - Request ID
 * @param {string} reason - Optional rejection reason
 * @returns {Promise<Object>} Updated request
 */
export async function rejectTimeOffRequest(requestId, reason = '') {
  const response = await apiClient.post(`/time-off/requests/${requestId}/reject`, { reason });
  return response.data;
}

/**
 * Delete a time-off request (only PENDING requests)
 * @param {number} requestId - Request ID
 * @returns {Promise<void>}
 */
export async function deleteTimeOffRequest(requestId) {
  await apiClient.delete(`/time-off/requests/${requestId}`);
}

/**
 * Get current user's time-off requests
 * @returns {Promise<Array>} List of user's requests
 */
export async function fetchMyTimeOffRequests() {
  // Backend should filter by current user automatically
  const response = await apiClient.get('/time-off/requests/');
  return response.data;
}
