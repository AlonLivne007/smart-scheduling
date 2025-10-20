/**
 * Home Page Component
 * 
 * The main dashboard page that provides an overview of the workforce management system.
 * Displays key metrics, welcome message, and quick actions for users.
 * 
 * Features:
 * - Large branded logo with subtitle
 * - Welcome card with call-to-action buttons
 * - Key metrics cards (employees, shifts, coverage)
 * - Recent activity section
 * - Responsive grid layout
 * 
 * @component
 * @returns {JSX.Element} The home dashboard page
 */
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import Logo from '../components/ui/Logo.jsx';
import MetricCard from '../components/ui/MetricCard.jsx';
import PageLayout from '../layouts/PageLayout.jsx';
import { Users, Clock, TrendingUp, Activity } from 'lucide-react';

export default function Home() {
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
              <div className="flex gap-3">
                <Button variant="primary">Get Started</Button>
                <Button variant="successSolid">Learn More</Button>
              </div>
            </div>
          </div>
        
          {/* Metrics Cards - Key performance indicators */}
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<Users className="w-6 h-6 text-blue-600" />}
              title="Total Employees"
              value="120"
              description="Active team members"
            />
          </div>
          
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<Clock className="w-6 h-6 text-blue-600" />}
              title="Upcoming Shifts"
              value="24"
              description="Next 7 days"
            />
          </div>
          
          <div className="lg:col-span-4">
            <MetricCard 
              icon={<TrendingUp className="w-6 h-6 text-blue-600" />}
              title="Coverage Rate"
              value="96%"
              description="This week"
            />
          </div>
        
          {/* Recent Activity Section - Shows latest system activity */}
          <div className="lg:col-span-12">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No recent activity</p>
              </div>
            </div>
          </div>
        </div>
    </PageLayout>
  )
}


