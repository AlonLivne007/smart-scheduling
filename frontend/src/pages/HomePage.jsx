/**
 * Home Page Component
 * 
 * The main dashboard page that provides an overview of the workforce management system.
 * Displays key metrics, welcome message, and quick actions for users.
 * 
 * Features:
 * - Large branded logo with subtitle
 * - Welcome card with call-to-action buttons
 * - Key metrics cards (employees, shifts, coverage) with loading skeleton state
 * - Recent activity section
 * - Responsive grid layout
 * 
 * @component
 * @returns {JSX.Element} The home dashboard page
 */
import { useEffect, useState } from 'react';
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import Logo from '../components/ui/Logo.jsx';
import MetricCard from '../components/ui/MetricCard.jsx';
import ActivityFeed from '../components/ActivityFeed.jsx';
import WeeklyScheduleWidget from '../components/WeeklyScheduleWidget.jsx';
import PageLayout from '../layouts/PageLayout.jsx';
import { showSuccess, showError } from '../lib/notifications.jsx';
import { fetchAllMetrics } from '../api/metrics.js';
import { fetchRecentActivities } from '../api/activity.js';
import { fetchWeeklySchedule } from '../api/schedule.js';
import { Users, Clock, TrendingUp } from 'lucide-react';

export default function Home() {
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [scheduleLoading, setScheduleLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    totalEmployees: 0,
    upcomingShifts: 0,
    coverageRate: 0,
  });
  const [activities, setActivities] = useState([]);
  const [schedule, setSchedule] = useState({
    days: [],
    totalShifts: 0,
    weeklyFillRate: 0,
  });

  useEffect(() => {
    // Show welcome notification on page load (only once due to dependency array)
    const timer = setTimeout(() => {
      showSuccess('Welcome back! Dashboard loaded successfully.');
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  // Simulate fetching metrics data
  useEffect(() => {
    const loadMetrics = async () => {
      try {
        setMetricsLoading(true);
        
        // Fetch metrics from backend API
        const data = await fetchAllMetrics();
        
        setMetrics({
          totalEmployees: data.totalEmployees,
          upcomingShifts: data.upcomingShifts,
          coverageRate: data.coverageRate,
        });
        setMetricsLoading(false);
      } catch (error) {
        console.error('Failed to load metrics:', error);
        showError('Failed to load dashboard metrics. Please try again.');
        setMetricsLoading(false);
      }
    };

    const loadActivities = async () => {
      try {
        setActivitiesLoading(true);
        const data = await fetchRecentActivities(5);
        setActivities(data);
        setActivitiesLoading(false);
      } catch (error) {
        console.error('Failed to load activities:', error);
        setActivitiesLoading(false);
      }
    };

    const loadSchedule = async () => {
      try {
        setScheduleLoading(true);
        const data = await fetchWeeklySchedule();
        setSchedule({
          days: data.days,
          totalShifts: data.totalShifts,
          weeklyFillRate: data.weeklyFillRate,
        });
        setScheduleLoading(false);
      } catch (error) {
        console.error('Failed to load schedule:', error);
        setScheduleLoading(false);
      }
    };
    
    loadMetrics();
    loadActivities();
    loadSchedule();
  }, []);

  return (
    <PageLayout>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Header Section - Logo and subtitle */}
          <div className="lg:col-span-12">
            <div className="text-center mb-8">
              <div className="mb-6 flex justify-center">
                <Logo size="large" showText={false} className="w-20 h-20" />
              </div>
              <h1 className="text-4xl font-bold text-blue-700 mb-2">
                Smart Scheduling
              </h1>
              <p className="text-lg text-blue-500 font-light">
                Workforce Management Dashboard
              </p>
            </div>
          </div>
        
          {/* Welcome Card - Main call-to-action section */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
              <h2 className="text-2xl font-bold text-blue-600 mb-2">Welcome to your dashboard</h2>
              <p className="text-gray-600 mb-6">Manage your workforce efficiently with our smart scheduling system.</p>
              <div className="flex gap-3 flex-wrap">
                <Button variant="primary" onClick={() => showSuccess('Feature coming soon!')}>Get Started</Button>
                <Button variant="successSolid" onClick={() => showSuccess('Learn more section coming soon!')}>Learn More</Button>
              </div>
            </div>
          </div>
        
          {/* Metrics Cards - Key performance indicators */}
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<Users className="w-6 h-6 text-blue-600" />}
              title="Total Employees"
              value={metrics.totalEmployees}
              description="Active team members"
              isLoading={metricsLoading}
            />
          </div>
          
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<Clock className="w-6 h-6 text-blue-600" />}
              title="Upcoming Shifts"
              value={metrics.upcomingShifts}
              description="Next 7 days"
              isLoading={metricsLoading}
            />
          </div>
          
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<TrendingUp className="w-6 h-6 text-blue-600" />}
              title="Coverage Rate"
              value={`${metrics.coverageRate}%`}
              description="This week"
              isLoading={metricsLoading}
            />
          </div>
        
          {/* Recent Activity Section - Shows latest system activity */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <ActivityFeed 
                activities={activities}
                isLoading={activitiesLoading}
                showViewAll={true}
                onViewAll={() => showSuccess('View all activities coming soon!')}
              />
            </div>
          </div>

          {/* Weekly Schedule Section - Next week's shift overview */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Next Week's Schedule</h3>
              <WeeklyScheduleWidget
                weekData={schedule.days}
                isLoading={scheduleLoading}
                totalShifts={schedule.totalShifts}
                weeklyFillRate={schedule.weeklyFillRate}
                onDayClick={(date) => {
                  showSuccess(`Selected ${date} - Schedule drill-down coming soon!`);
                }}
              />
            </div>
          </div>
        </div>
    </PageLayout>
  )
}


