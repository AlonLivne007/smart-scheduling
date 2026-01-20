/**
 * Home Page Component
 * 
 * Merged dashboard showing welcome message and employee's shift assignments.
 * Displays current week schedule with shift details and weekly summary.
 * 
 * @component
 * @returns {JSX.Element} The home dashboard page
 */
import { useEffect, useState } from 'react';
import { format, addDays, startOfWeek, parseISO } from 'date-fns';
import { Calendar, Clock, MapPin, User, ChevronLeft, ChevronRight, Briefcase, CalendarDays } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../lib/axios';
import Card from '../components/ui/Card.jsx';
import Button from '../components/ui/Button.jsx';
import PageLayout from '../layouts/PageLayout.jsx';
import { getAuth } from '../lib/auth';

export default function Home() {
  const { user } = getAuth();
  const [loading, setLoading] = useState(true);
  const [myShifts, setMyShifts] = useState([]);
  const [timeOffRequests, setTimeOffRequests] = useState([]);
  const [currentWeekStart, setCurrentWeekStart] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }));

  useEffect(() => {
    if (user?.user_id) {
      loadMyShifts();
      loadTimeOffRequests();
    } else {
      setLoading(false);
    }
  }, [user?.user_id, currentWeekStart]);

  async function loadMyShifts() {
    if (!user?.user_id) return;

    try {
      setLoading(true);
      console.log('Loading shifts for user:', user.user_id);
      const { data: assignments } = await api.get(`/shift-assignments/user/${user.user_id}`);
      console.log('Assignments loaded:', assignments.length);
      
      const shiftsWithDetails = await Promise.all(
        assignments.map(async (assignment) => {
          try {
            const { data: plannedShift } = await api.get(`/planned-shifts/${assignment.planned_shift_id}`);
            const { data: schedule } = await api.get(`/weekly-schedules/${plannedShift.weekly_schedule_id}`);
            
            return {
              ...assignment,
              shift: plannedShift,
              schedule: schedule
            };
          } catch (error) {
            console.error(`Failed to load shift ${assignment.planned_shift_id}:`, error);
            return null;
          }
        })
      );

      const validShifts = shiftsWithDetails.filter(s => 
        s && s.shift && s.schedule && s.schedule.status === 'PUBLISHED'
      );
      console.log('Valid shifts:', validShifts.length);
      
      const weekEnd = addDays(currentWeekStart, 6);
      const weekShifts = validShifts.filter(s => {
        const shiftDate = parseISO(s.shift.date);
        return shiftDate >= currentWeekStart && shiftDate <= weekEnd;
      });
      console.log('Week shifts:', weekShifts.length);

      setMyShifts(weekShifts);
    } catch (error) {
      console.error('Failed to load shifts:', error);
      toast.error('Failed to load your schedule');
    } finally {
      setLoading(false);
    }
  }

  async function loadTimeOffRequests() {
    if (!user?.user_id) return;

    try {
      const { data } = await api.get(`/time-off-requests/?user_id=${user.user_id}`);
      const pending = data.filter(req => req.status === 'PENDING');
      setTimeOffRequests(pending);
    } catch (error) {
      console.error('Failed to load time off requests:', error);
    }
  }

  function getShiftsForDay(dayIndex) {
    const targetDate = format(addDays(currentWeekStart, dayIndex), 'yyyy-MM-dd');
    return myShifts.filter(s => s.shift.date === targetDate);
  }

  function goToPreviousWeek() {
    setCurrentWeekStart(prev => addDays(prev, -7));
  }

  function goToNextWeek() {
    setCurrentWeekStart(prev => addDays(prev, 7));
  }

  function goToCurrentWeek() {
    setCurrentWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }));
  }

  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  const totalHours = myShifts.reduce((total, s) => {
    const start = parseISO(s.shift.start_time);
    const end = parseISO(s.shift.end_time);
    const hours = (end - start) / (1000 * 60 * 60);
    return total + hours;
  }, 0);

  const daysWorking = new Set(myShifts.map(s => s.shift.date)).size;

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg p-8 text-white">
          <div className="flex items-center gap-3 mb-3">
            <Calendar className="h-8 w-8" />
            <h1 className="text-3xl font-bold">Welcome back, {user?.user_full_name}!</h1>
          </div>
          <p className="text-blue-100 text-lg">
            {format(new Date(), 'EEEE, MMMM d, yyyy')}
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Briefcase className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <div className="text-sm text-gray-600">This Week</div>
                  <div className="text-2xl font-bold text-gray-900">{myShifts.length}</div>
                  <div className="text-xs text-gray-500">shifts</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-green-100 p-3 rounded-lg">
                  <Clock className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <div className="text-sm text-gray-600">Total Hours</div>
                  <div className="text-2xl font-bold text-gray-900">{totalHours.toFixed(1)}</div>
                  <div className="text-xs text-gray-500">hours</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <CalendarDays className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <div className="text-sm text-gray-600">Days Working</div>
                  <div className="text-2xl font-bold text-gray-900">{daysWorking}</div>
                  <div className="text-xs text-gray-500">days</div>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="flex items-center gap-3">
                <div className="bg-orange-100 p-3 rounded-lg">
                  <Calendar className="h-6 w-6 text-orange-600" />
                </div>
                <div>
                  <div className="text-sm text-gray-600">Time Off</div>
                  <div className="text-2xl font-bold text-gray-900">{timeOffRequests.length}</div>
                  <div className="text-xs text-gray-500">pending</div>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Week Navigation */}
        <div className="bg-white rounded-xl shadow p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {format(currentWeekStart, 'MMMM d')} - {format(addDays(currentWeekStart, 6), 'MMMM d, yyyy')}
            </h2>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={goToPreviousWeek}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" onClick={goToCurrentWeek}>
                Today
              </Button>
              <Button variant="outline" onClick={goToNextWeek}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Week Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading your schedule...</p>
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-4">
            {weekDays.map((day, index) => {
              const dayDate = addDays(currentWeekStart, index);
              const shiftsForDay = getShiftsForDay(index);
              const isToday = format(dayDate, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');

              return (
                <div
                  key={day}
                  className={`bg-white rounded-lg shadow ${
                    isToday ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className={`p-3 border-b ${
                    isToday ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'
                  }`}>
                    <div className="font-semibold text-sm text-gray-900">{day}</div>
                    <div className={`text-xs ${isToday ? 'text-blue-600' : 'text-gray-500'}`}>
                      {format(dayDate, 'MMM d')}
                    </div>
                  </div>
                  
                  <div className="p-2 space-y-2 min-h-[200px]">
                    {shiftsForDay.length === 0 ? (
                      <div className="text-center py-8 text-gray-400 text-sm">
                        No shifts
                      </div>
                    ) : (
                      shiftsForDay.map(assignment => (
                        <div
                          key={assignment.assignment_id}
                          className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm"
                        >
                          <div className="font-semibold text-blue-900 mb-2">
                            {assignment.shift.shift_template_name || 'Shift'}
                          </div>
                          
                          <div className="space-y-1 text-xs text-gray-700">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>
                                {format(parseISO(assignment.shift.start_time), 'HH:mm')} - {format(parseISO(assignment.shift.end_time), 'HH:mm')}
                              </span>
                            </div>
                            
                            {assignment.shift.location && (
                              <div className="flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                <span>{assignment.shift.location}</span>
                              </div>
                            )}
                            
                            {assignment.role_name && (
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                <span>{assignment.role_name}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Empty State */}
        {!loading && myShifts.length === 0 && (
          <Card>
            <div className="text-center py-12">
              <Calendar className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No shifts this week</h3>
              <p className="text-gray-500">You don't have any shifts scheduled for this week.</p>
            </div>
          </Card>
        )}
      </div>
    </PageLayout>
  );
}


