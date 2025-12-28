/**
 * WeeklyScheduleWidget Component
 * 
 * Displays a week-at-a-glance view of the upcoming schedule showing:
 * - Planned shifts per day
 * - Assigned vs unassigned positions
 * - Days with coverage gaps highlighted
 * - Click to view/filter by day
 * 
 * Features:
 * - Monday through Sunday view
 * - Color-coded based on fill rate
 * - Responsive grid layout
 * - Weekly summary statistics
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Array} props.weekData - Array of 7 day objects with shift/assignment data
 * @param {boolean} props.isLoading - Whether data is loading
 * @param {number} props.totalShifts - Total shifts for the week
 * @param {number} props.weeklyFillRate - Overall fill rate percentage
 * @param {Function} props.onDayClick - Callback when day is clicked
 * 
 * @example
 * <WeeklyScheduleWidget
 *   weekData={weekData}
 *   totalShifts={24}
 *   weeklyFillRate={85}
 *   onDayClick={(date) => navigate(`/schedule?date=${date}`)}
 * />
 */

import React from 'react';
import { ChevronRight } from 'lucide-react';
import Skeleton from './ui/Skeleton.jsx';

function WeeklyScheduleWidget({
  weekData = [],
  isLoading = false,
  totalShifts = 0,
  weeklyFillRate = 0,
  onDayClick = () => {},
}) {
  // Loading skeleton
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-7 gap-2">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton size="small" width="100%" />
              <Skeleton size="small" width="100%" />
              <Skeleton size="small" width="100%" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Get fill rate color based on percentage
  const getFillRateColor = (rate) => {
    if (rate >= 90) return 'bg-green-50 border-green-300';
    if (rate >= 75) return 'bg-blue-50 border-blue-300';
    if (rate >= 50) return 'bg-yellow-50 border-yellow-300';
    return 'bg-red-50 border-red-300';
  };

  const getTextColor = (rate) => {
    if (rate >= 90) return 'text-green-700';
    if (rate >= 75) return 'text-blue-700';
    if (rate >= 50) return 'text-yellow-700';
    return 'text-red-700';
  };

  return (
    <div className="space-y-4">
      {/* Weekly Summary */}
      <div className="flex justify-between items-center px-1">
        <div>
          <p className="text-sm text-gray-600">Total Shifts</p>
          <p className="text-2xl font-bold text-gray-900">{totalShifts}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Weekly Fill Rate</p>
          <p className={`text-2xl font-bold ${getTextColor(weeklyFillRate)}`}>
            {weeklyFillRate}%
          </p>
        </div>
      </div>

      {/* Daily Grid */}
      <div className="grid grid-cols-7 gap-2">
        {weekData.map((day, idx) => (
          <button
            key={idx}
            onClick={() => onDayClick(day.dateStr)}
            className={`p-3 rounded-lg border-2 transition-all hover:shadow-md ${getFillRateColor(
              day.fillRate
            )} cursor-pointer`}
          >
            {/* Day name and date */}
            <div className="text-center mb-2">
              <p className="text-xs font-semibold text-gray-700">{day.dayName}</p>
              <p className="text-sm font-bold text-gray-900">{day.dayNum}</p>
            </div>

            {/* Shift counts */}
            <div className="space-y-1 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Shifts:</span>
                <span className="font-semibold text-gray-900">{day.plannedShifts}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Assigned:</span>
                <span className="font-semibold text-green-700">{day.assignedCount}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Needed:</span>
                <span className={`font-semibold ${day.hasGaps ? 'text-red-700' : 'text-gray-700'}`}>
                  {day.requiredCount}
                </span>
              </div>
            </div>

            {/* Gap indicator */}
            {day.hasGaps && (
              <div className="mt-2 pt-2 border-t border-red-300 flex items-center justify-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-xs font-semibold text-red-700">Gap</span>
              </div>
            )}

            {/* Fill rate bar */}
            <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-green-400 to-blue-500 h-full transition-all"
                style={{ width: `${Math.min(100, day.fillRate)}%` }}
              />
            </div>

            {/* Fill rate percentage */}
            <p className="text-xs font-semibold text-center mt-1 text-gray-700">
              {day.fillRate}%
            </p>
          </button>
        ))}
      </div>

      {/* View Full Schedule Link */}
      <button
        onClick={() => onDayClick('week')}
        className="w-full flex items-center justify-center gap-2 text-blue-600 hover:text-blue-700 font-medium py-2 px-3 rounded-lg hover:bg-blue-50 transition-colors text-sm"
      >
        View Full Schedule
        <ChevronRight className="w-4 h-4" />
      </button>

      {/* Legend */}
      <div className="grid grid-cols-4 gap-2 text-xs text-gray-600 px-1">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-green-400 rounded"></div>
          <span>90%+</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-blue-400 rounded"></div>
          <span>75-90%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-yellow-400 rounded"></div>
          <span>50-75%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-red-400 rounded"></div>
          <span>&lt;50%</span>
        </div>
      </div>
    </div>
  );
}

export default WeeklyScheduleWidget;
