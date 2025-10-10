import { Button, Card, Logo } from '../components/ui';

export default function Home() {
  return (
    <div className="container-fluid py-4">
      <div className="row g-4">
        <div className="col-12">
          <div className="d-flex align-items-center mb-4">
            <Logo size="large" />
            <div className="ms-3">
              <p className="text-muted mb-0">Workforce Management Dashboard</p>
            </div>
          </div>
        </div>
        
        <div className="col-12">
          <Card className="mb-4" padding="large">
            <Card.Title className="text-primary">Welcome to your dashboard</Card.Title>
            <Card.Text>Manage your workforce efficiently with our smart scheduling system.</Card.Text>
            <div className="d-flex gap-3 mt-3">
              <Button variant="primary" size="large">Get Started</Button>
              <Button variant="success" size="large">Learn More</Button>
            </div>
          </Card>
        </div>
        
        <div className="col-md-4">
          <Card hover className="h-100">
            <Card.Body className="text-center">
              <div className="bg-primary bg-opacity-10 rounded-circle p-3 d-inline-block mb-3">
                <i className="bi bi-people text-primary fs-3"></i>
              </div>
              <Card.Title>Total Employees</Card.Title>
              <h2 className="display-6 fw-bold text-primary">120</h2>
              <Card.Text>Active team members</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        <div className="col-md-4">
          <Card hover className="h-100">
            <Card.Body className="text-center">
              <div className="bg-primary bg-opacity-10 rounded-circle p-3 d-inline-block mb-3">
                <i className="bi bi-clock text-primary fs-3"></i>
              </div>
              <Card.Title>Upcoming Shifts</Card.Title>
              <h2 className="display-6 fw-bold text-primary">24</h2>
              <Card.Text>Next 7 days</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        <div className="col-md-4">
          <Card hover className="h-100">
            <Card.Body className="text-center">
              <div className="bg-primary bg-opacity-10 rounded-circle p-3 d-inline-block mb-3">
                <i className="bi bi-graph-up text-primary fs-3"></i>
              </div>
              <Card.Title>Coverage Rate</Card.Title>
              <h2 className="display-6 fw-bold text-primary">96%</h2>
              <Card.Text>This week</Card.Text>
            </Card.Body>
          </Card>
        </div>
        
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Recent Activity</Card.Title>
            </Card.Header>
            <Card.Body>
              <div className="text-center py-5">
                <i className="bi bi-activity text-muted fs-1 mb-3"></i>
                <p className="text-muted">No recent activity</p>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  )
}


