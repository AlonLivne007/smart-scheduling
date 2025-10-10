import { Button, Card } from '../components/ui';

export default function TestPage() {
  return (
    <div className="container-fluid py-4">
      <div className="row g-4">
        {/* Header Section */}
        <div className="col-12">
          <div className="d-flex align-items-center justify-content-between">
            <div>
              <h1 className="display-4 fw-bold text-primary mb-2">UI Kit Test Page</h1>
              <p className="lead text-muted">Testing all components and layouts</p>
            </div>
            <div className="d-flex gap-2">
              <Button variant="primary" size="large">
                <i className="bi bi-check-circle me-2"></i>Primary Action
              </Button>
              <Button variant="secondary" size="large">
                <i className="bi bi-gear me-2"></i>Secondary
              </Button>
            </div>
          </div>
        </div>

        {/* Button Variants */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Button Variants</Card.Title>
              <Card.Text>All button styles and sizes</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-3">
                <div className="col-md-6">
                  <h6 className="fw-semibold mb-3">Button Variants</h6>
                  <div className="d-flex flex-wrap gap-2 mb-4">
                    <Button variant="primary">Primary</Button>
                    <Button variant="success">Success</Button>
                    <Button variant="danger">Danger</Button>
                  </div>
                </div>
                <div className="col-md-6">
                  <h6 className="fw-semibold mb-3">Button Sizes</h6>
                  <div className="d-flex flex-wrap gap-2 align-items-center">
                    <Button variant="primary" size="small">Small</Button>
                    <Button variant="primary" size="medium">Medium</Button>
                    <Button variant="primary" size="large">Large</Button>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Card Variants */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Card Variants</Card.Title>
              <Card.Text>Different card styles and layouts</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-4">
                <div className="col-md-4">
                  <Card variant="default" hover>
                    <Card.Body className="text-center">
                      <div className="bg-primary bg-opacity-10 rounded-circle p-3 d-inline-block mb-3">
                        <i className="bi bi-heart text-primary fs-3"></i>
                      </div>
                      <Card.Title>Default Card</Card.Title>
                      <Card.Text>Standard card with hover effect</Card.Text>
                    </Card.Body>
                  </Card>
                </div>
                <div className="col-md-4">
                  <Card variant="primary" hover>
                    <Card.Body className="text-center">
                      <div className="bg-white bg-opacity-20 rounded-circle p-3 d-inline-block mb-3">
                        <i className="bi bi-star text-white fs-3"></i>
                      </div>
                      <Card.Title className="text-white">Primary Card</Card.Title>
                      <Card.Text className="text-white">Blue gradient background</Card.Text>
                    </Card.Body>
                  </Card>
                </div>
                <div className="col-md-4">
                  <Card variant="light" hover>
                    <Card.Body className="text-center">
                      <div className="bg-primary bg-opacity-20 rounded-circle p-3 d-inline-block mb-3">
                        <i className="bi bi-lightning text-primary fs-3"></i>
                      </div>
                      <Card.Title>Light Card</Card.Title>
                      <Card.Text>Light blue background</Card.Text>
                    </Card.Body>
                  </Card>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Dashboard Layout Test */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Dashboard Layout</Card.Title>
              <Card.Text>Testing the dashboard card layout</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-4">
                <div className="col-md-3">
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
                <div className="col-md-3">
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
                <div className="col-md-3">
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
                <div className="col-md-3">
                  <Card hover className="h-100">
                    <Card.Body className="text-center">
                      <div className="bg-primary bg-opacity-10 rounded-circle p-3 d-inline-block mb-3">
                        <i className="bi bi-calendar-check text-primary fs-3"></i>
                      </div>
                      <Card.Title>Completed</Card.Title>
                      <h2 className="display-6 fw-bold text-primary">156</h2>
                      <Card.Text>This month</Card.Text>
                    </Card.Body>
                  </Card>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Form Elements */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Form Elements</Card.Title>
              <Card.Text>Input fields and form components</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-4">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Email Address</label>
                    <input type="email" className="form-control rounded-3 border-light" placeholder="Enter your email" />
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Password</label>
                    <input type="password" className="form-control rounded-3 border-light" placeholder="Enter your password" />
                  </div>
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Select Option</label>
                    <select className="form-select rounded-3 border-light">
                      <option>Choose an option</option>
                      <option>Option 1</option>
                      <option>Option 2</option>
                    </select>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="mb-3">
                    <label className="form-label fw-semibold">Message</label>
                    <textarea className="form-control rounded-3 border-light" rows="4" placeholder="Enter your message"></textarea>
                  </div>
                  <div className="form-check mb-3">
                    <input className="form-check-input" type="checkbox" id="check1" />
                    <label className="form-check-label" htmlFor="check1">
                      Remember me
                    </label>
                  </div>
                  <div className="form-check">
                    <input className="form-check-input" type="radio" name="radio1" id="radio1" />
                    <label className="form-check-label" htmlFor="radio1">
                      Option 1
                    </label>
                  </div>
                </div>
              </div>
              <div className="d-flex gap-2 mt-4">
                <Button variant="primary">Save Changes</Button>
                <Button variant="success">Cancel</Button>
                <Button variant="danger">Reset</Button>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Color Palette */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Color Palette</Card.Title>
              <Card.Text>Blue theme colors and variations</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-3">
                <div className="col-md-2">
                  <div className="bg-primary rounded-3 p-4 text-center text-white">
                    <strong>Primary</strong>
                    <br />
                    <small>#2563eb</small>
                  </div>
                </div>
                <div className="col-md-2">
                  <div className="bg-light rounded-3 p-4 text-center">
                    <strong>Light</strong>
                    <br />
                    <small>#eff6ff</small>
                  </div>
                </div>
                <div className="col-md-2">
                  <div className="bg-gradient rounded-3 p-4 text-center text-white">
                    <strong>Gradient</strong>
                    <br />
                    <small>Blue mix</small>
                  </div>
                </div>
                <div className="col-md-2">
                  <div className="border border-primary rounded-3 p-4 text-center">
                    <strong>Outline</strong>
                    <br />
                    <small>Border only</small>
                  </div>
                </div>
                <div className="col-md-2">
                  <div className="bg-white border border-light rounded-3 p-4 text-center">
                    <strong>White</strong>
                    <br />
                    <small>#ffffff</small>
                  </div>
                </div>
                <div className="col-md-2">
                  <div className="bg-muted rounded-3 p-4 text-center text-white">
                    <strong>Muted</strong>
                    <br />
                    <small>#64748b</small>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Typography */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Typography</Card.Title>
              <Card.Text>Text styles and hierarchy</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-4">
                <div className="col-md-6">
                  <h1 className="display-1 text-primary">Display 1</h1>
                  <h2 className="display-2 text-primary">Display 2</h2>
                  <h3 className="display-3 text-primary">Display 3</h3>
                  <h4 className="display-4 text-primary">Display 4</h4>
                </div>
                <div className="col-md-6">
                  <h1>Heading 1</h1>
                  <h2>Heading 2</h2>
                  <h3>Heading 3</h3>
                  <h4>Heading 4</h4>
                  <h5>Heading 5</h5>
                  <h6>Heading 6</h6>
                  <p className="lead">This is a lead paragraph with larger text.</p>
                  <p>This is a regular paragraph with normal text size.</p>
                  <p className="text-muted">This is muted text for secondary information.</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Interactive Elements */}
        <div className="col-12">
          <Card>
            <Card.Header>
              <Card.Title>Interactive Elements</Card.Title>
              <Card.Text>Hover effects and animations</Card.Text>
            </Card.Header>
            <Card.Body>
              <div className="row g-4">
                <div className="col-md-4">
                  <Card hover className="text-center">
                    <Card.Body>
                      <i className="bi bi-magic text-primary fs-1 mb-3"></i>
                      <Card.Title>Hover Card</Card.Title>
                      <Card.Text>This card lifts on hover</Card.Text>
                    </Card.Body>
                  </Card>
                </div>
                <div className="col-md-4">
                  <div className="text-center">
                    <Button variant="primary" size="large" className="me-2">
                      <i className="bi bi-arrow-right me-2"></i>Hover Me
                    </Button>
                    <p className="text-muted mt-2">Button with hover effects</p>
                  </div>
                </div>
                <div className="col-md-4">
                  <div className="bg-light rounded-3 p-4 text-center hover-lift">
                    <i className="bi bi-sparkles text-primary fs-1 mb-3"></i>
                    <h5>Lift Effect</h5>
                    <p className="text-muted mb-0">This element lifts on hover</p>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  )
}
