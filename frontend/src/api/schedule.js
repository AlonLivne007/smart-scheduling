/**
 * Schedule API Helpers
 * 
 * Functions to fetch and calculate weekly schedule data for the dashboard.
 * 
 * @module api/schedule
 */

import api from '../lib/axios.js';

/**
 * Get the start of the next week (Monday)
 * @returns {Date} Monday of next week
 */
const getNextWeekMonday = () => {
  const today = new Date();
  const currentDay = today.getDay();
  const daysUntilMonday = currentDay === 0 ? 1 : 8 - currentDay;
  const nextMonday = new Date(today);
  nextMonday.setDate(nextMonday.getDate() + daysUntilMonday);
  nextMonday.setHours(0, 0, 0, 0);
  return nextMonday;
};

/**
 * Format date to YYYY-MM-DD string
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
const formatDateString = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Get day name from date
 * @param {Date} date - Date to get day name from
 * @returns {string} Day name (Mon, Tue, Wed, etc.)
 */
const getDayName = (date) => {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return dayNames[date.getDay()];
};

/**
 * Fetch weekly schedule data (next 7 days starting Monday)
 * 
 * @returns {Promise<Object>} Object with:
 *   - days: Array of 7 day objects with shift and assignment counts
 *   - totalShifts: Total planned shifts for the week
 *   - totalAssigned: Total assignments for the week
 *   - weeklyFillRate: Percentage of positions filled
 * @throws {Error} If API call fails
 */
export const fetchWeeklySchedule = async () => {
  try {
    const nextMonday = getNextWeekMonday();
    
    // Calculate all 7 days of the week
    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(nextMonday);
      date.setDate(date.getDate() + i);
      weekDays.push(date);
    }

    // Fetch all planned shifts for the week
    const shiftsResponse = await api.get('/planned-shifts/');
    const assignmentsResponse = await api.get('/shift-assignments/');

    const allShifts = shiftsResponse.data || [];
    const allAssignments = assignmentsResponse.data || [];

    // Build map of assignments by shift_id for quick lookup
    const assignmentsByShift = {};
    allAssignments.forEach((assignment) => {
      if (!assignmentsByShift[assignment.planned_shift_id]) {
        assignmentsByShift[assignment.planned_shift_id] = [];
      }
      assignmentsByShift[assignment.planned_shift_id].push(assignment);
    });

    // Calculate daily stats
    const days = weekDays.map((date) => {
      const dateStr = formatDateString(date);
      const dayName = getDayName(date);
      const dayNum = date.getDate();

      // Filter shifts for this day
      const dayShifts = allShifts.filter((shift) => {
        const shiftDate = new Date(shift.date || shift.shift_date || shift.scheduled_date);
        return formatDateString(shiftDate) === dateStr;
      });

      // Count assignments for this day
      let assignedCount = 0;
      dayShifts.forEach((shift) => {
        assignedCount += (assignmentsByShift[shift.id] || []).length;
      });

      // Calculate required positions
      let requiredCount = 0;
      dayShifts.forEach((shift) => {
        if (shift.role_requirements && Array.isArray(shift.role_requirements)) {
          shift.role_requirements.forEach((req) => {
            requiredCount += req.required_count || 1;
          });
        } else {
          requiredCount += 1; // Default: 1 role required
        }
      });

      return {
        dayName,
        dayNum,
        date,
        dateStr,
        plannedShifts: dayShifts.length,
        assignedCount,
        requiredCount,
        unassignedCount: Math.max(0, requiredCount - assignedCount),
        hasGaps: requiredCount > assignedCount,
        fillRate: requiredCount > 0 ? Math.round((assignedCount / requiredCount) * 100) : 0,
      };
    });

    // Calculate weekly totals
    const totalShifts = days.reduce((sum, day) => sum + day.plannedShifts, 0);
    const totalAssigned = days.reduce((sum, day) => sum + day.assignedCount, 0);
    const totalRequired = days.reduce((sum, day) => sum + day.requiredCount, 0);
    const weeklyFillRate = totalRequired > 0 ? Math.round((totalAssigned / totalRequired) * 100) : 0;

    return {
      days,
      totalShifts,
      totalAssigned,
      totalRequired,
      weeklyFillRate,
    };
  } catch (error) {
    console.error('Error fetching weekly schedule:', error);
    throw error;
  }
};

/**
 * Get schedule for a specific day (for filtering)
 * 
 * @param {Date} date - Date to fetch schedule for
 * @returns {Promise<Array>} Array of shifts for the day
 * @throws {Error} If API call fails
 */
export const fetchScheduleByDay = async (date) => {
  try {
    const dateStr = formatDateString(date);
    const response = await api.get('/planned-shifts/');
    
    const dayShifts = (response.data || []).filter((shift) => {
      const shiftDate = new Date(shift.date || shift.shift_date || shift.scheduled_date);
      return formatDateString(shiftDate) === dateStr;
    });

    return dayShifts;
  } catch (error) {
    console.error(`Error fetching schedule for ${date}:`, error);
    throw error;
  }
};
