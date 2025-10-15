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
import { Button, Card, Logo } from '../components/ui';
import { Users, Clock, TrendingUp, Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="w-full py-6">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Header Section - Logo and subtitle */}
        <div className="lg:col-span-12">
          <div className="flex items-center mb-6">
            <Logo size="large" />
            <div className="ml-4">
              <p className="text-gray-600 mb-0">Workforce Management Dashboard</p>
            </div>
          </div>
          {/* Tailwind Test */}
          <div className="bg-blue-500 text-white p-4 rounded-lg mb-4">
            <p className="text-lg font-semibold">✅ Tailwind CSS is working!</p>
            <p className="text-sm opacity-90">This blue box confirms Tailwind styling is active.</p>
          </div>
        </div>
        
        {/* Welcome Card - Main call-to-action section */}
        <div className="lg:col-span-12">
          <Card className="mb-6" padding="large">
            <Card.Title className="text-blue-600">Welcome to your dashboard</Card.Title>
            <Card.Text>Manage your workforce efficiently with our smart scheduling system.</Card.Text>
            <div className="flex gap-3 mt-4">
              <Button variant="primary" size="large">Get Started</Button>
              <Button variant="success" size="large">Learn More</Button>
            </div>
          </Card>
        </div>
        
        {/* Metrics Cards - Key performance indicators */}
        <div className="lg:col-span-4">
          <Card hover className="h-full">
            <Card.Body className="text-center">
              <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <Card.Title>Total Employees</Card.Title>
              <h2 className="text-4xl font-bold text-blue-600">120</h2>
              <Card.Text>Active team members</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        <div className="lg:col-span-4">
          <Card hover className="h-full">
            <Card.Body className="text-center">
              <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
              <Card.Title>Upcoming Shifts</Card.Title>
              <h2 className="text-4xl font-bold text-blue-600">24</h2>
              <Card.Text>Next 7 days</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        <div className="lg:col-span-4">
          <Card hover className="h-full">
            <Card.Body className="text-center">
              <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <Card.Title>Coverage Rate</Card.Title>
              <h2 className="text-4xl font-bold text-blue-600">96%</h2>
              <Card.Text>This week</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        {/* Recent Activity Section - Shows latest system activity */}
        <div className="lg:col-span-12">
          <Card>
            <Card.Header>
              <Card.Title>Recent Activity</Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No recent activity</p>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  )
}


