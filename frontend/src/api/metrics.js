/**
 * Metrics API Helpers
 * 
 * Functions to fetch dashboard metrics from the backend API.
 * Includes employee count, upcoming shifts, and coverage rate calculations.
 * 
 * @module api/metrics
 */

import api from '../lib/axios.js';

/**
 * Fetch total number of active employees
 * @returns {Promise<number>} Total employee count
 * @throws {Error} If API call fails
 */
export const fetchTotalEmployees = async () => {
  try {
    const response = await api.get('/users/');
    return response.data.length || 0;
  } catch (error) {
    console.error('Error fetching total employees:', error);
    throw error;
  }
};

/**
 * Fetch upcoming shifts for the next 7 days
 * @returns {Promise<number>} Number of upcoming shifts
 * @throws {Error} If API call fails
 */
export const fetchUpcomingShifts = async () => {
  try {
    // Get today's date and 7 days from now
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    nextWeek.setHours(23, 59, 59, 999);

    // Fetch all planned shifts and filter by date range
    const response = await api.get('/planned-shifts/');
    
    const upcomingShifts = response.data.filter((shift) => {
      // Parse shift date - handle both ISO string and other formats
      const shiftDate = new Date(shift.date || shift.shift_date || shift.scheduled_date);
      shiftDate.setHours(0, 0, 0, 0);
      return shiftDate >= today && shiftDate <= nextWeek;
    });

    return upcomingShifts.length || 0;
  } catch (error) {
    console.error('Error fetching upcoming shifts:', error);
    throw error;
  }
};

/**
 * Calculate coverage rate as percentage of assigned vs required positions
 * 
 * Formula: (total assignments / total required assignments) * 100
 * 
 * @returns {Promise<number>} Coverage percentage (0-100)
 * @throws {Error} If API call fails
 */
export const fetchCoverageRate = async () => {
  try {
    // Fetch all shift assignments and planned shifts
    const [assignmentsResponse, shiftsResponse] = await Promise.all([
      api.get('/shift-assignments/'),
      api.get('/planned-shifts/'),
    ]);

    const assignments = assignmentsResponse.data || [];
    const shifts = shiftsResponse.data || [];

    // Calculate total required positions
    let totalRequired = 0;
    shifts.forEach((shift) => {
      // Get role requirements for this shift
      if (shift.role_requirements && Array.isArray(shift.role_requirements)) {
        shift.role_requirements.forEach((req) => {
          totalRequired += req.required_count || 1;
        });
      } else {
        // Default: assume 1 role required per shift if no role requirements data
        totalRequired += 1;
      }
    });

    // If no required positions, return 0
    if (totalRequired === 0) {
      return 0;
    }

    // Calculate coverage rate
    const totalAssigned = assignments.length;
    const coverageRate = (totalAssigned / totalRequired) * 100;

    // Return as whole number percentage (0-100)
    return Math.round(Math.min(coverageRate, 100));
  } catch (error) {
    console.error('Error fetching coverage rate:', error);
    throw error;
  }
};

/**
 * Fetch all dashboard metrics at once
 * 
 * @returns {Promise<Object>} Object with totalEmployees, upcomingShifts, and coverageRate
 * @throws {Error} If any API call fails
 */
export const fetchAllMetrics = async () => {
  try {
    const [employees, shifts, coverage] = await Promise.all([
      fetchTotalEmployees(),
      fetchUpcomingShifts(),
      fetchCoverageRate(),
    ]);

    return {
      totalEmployees: employees,
      upcomingShifts: shifts,
      coverageRate: coverage,
    };
  } catch (error) {
    console.error('Error fetching all metrics:', error);
    throw error;
  }
};
