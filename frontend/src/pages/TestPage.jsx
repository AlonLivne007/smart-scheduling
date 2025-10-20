/**
 * TestPage Component
 * 
 * A comprehensive UI testing page that showcases all available components and design elements.
 * This page is used for development and testing purposes to verify component functionality
 * and visual consistency across the application.
 * 
 * Features:
 * - Button variants and sizes demonstration
 * - Card component variations and layouts
 * - Form elements and input styling
 * - Color palette showcase
 * - Typography hierarchy display
 * - Interactive elements and hover effects
 * - Responsive design testing
 * 
 * @component
 * @returns {JSX.Element} The comprehensive UI test page
 */
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import InputField from '../components/ui/InputField.jsx';

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-blue-700 mb-2">UI Kit Test Page</h1>
              <p className="text-lg text-blue-500 font-light">Testing all components and layouts</p>
            </div>
            <div className="flex gap-3">
              <Button variant="primary">Primary Action</Button>
              <Button variant="secondarySolid">Secondary</Button>
            </div>
          </div>
        </div>

        {/* Button Variants - showcases Button component variants and sizes */}
        <div className="mb-6">
          <Card padding="large" hover>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Button Variants</h3>
            <p className="text-gray-600 mb-6">All button styles and sizes</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Button Variants</h4>
                <div className="flex flex-wrap gap-3 mb-4">
                  <Button variant="primary">Primary</Button>
                  <Button variant="success">Success</Button>
                  <Button variant="danger">Danger</Button>
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Button Sizes</h4>
                <div className="flex flex-wrap gap-3 items-center">
                  <Button variant="primary" size="small">Small</Button>
                  <Button variant="primary" size="medium">Medium</Button>
                  <Button variant="primary" size="large">Large</Button>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Card Variants - showcases Card component variants */}
        <div className="mb-6">
          <Card padding="large" hover>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Card Variants</h3>
            <p className="text-gray-600 mb-6">Different card styles and layouts</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card padding="large" hover>
                <div className="text-center">
                  <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">♥</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Default Card</h4>
                  <p className="text-gray-600">Standard card with hover effect</p>
                </div>
              </Card>
              <Card variant="gradient" padding="large" hover>
                <div className="text-center">
                  <div className="bg-white bg-opacity-20 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-white rounded-full flex items-center justify-center">
                      <span className="text-blue-600 text-sm">★</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-white mb-2">Gradient Card</h4>
                  <p className="text-white">Blue gradient background</p>
                </div>
              </Card>
              <Card variant="light" padding="large" hover>
                <div className="text-center">
                  <div className="bg-blue-100 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">⚡</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Light Card</h4>
                  <p className="text-gray-600">Light blue background</p>
                </div>
              </Card>
              <Card variant="primary" padding="large" hover>
                <div className="text-center">
                  <div className="bg-blue-100 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">⚡</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Primary Card</h4>
                  <p className="text-gray-600">Primary blue background</p>
                </div>
              </Card>
            </div>
          </Card>
        </div>

        {/* Dashboard Layout Test - showcases Card in dashboard layout */}
        <div className="mb-6">
          <Card padding="large" hover>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Dashboard Layout</h3>
            <p className="text-gray-600 mb-6">Testing the dashboard card layout</p>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="h-full" hover padding="large">
                <div className="text-center">
                  <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">👥</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Total Employees</h4>
                  <h2 className="text-4xl font-bold text-blue-600 mb-2">120</h2>
                  <p className="text-gray-600">Active team members</p>
                </div>
              </Card>
              <Card className="h-full" hover padding="large">
                <div className="text-center">
                  <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">🕐</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Upcoming Shifts</h4>
                  <h2 className="text-4xl font-bold text-blue-600 mb-2">24</h2>
                  <p className="text-gray-600">Next 7 days</p>
                </div>
              </Card>
              <Card className="h-full" hover padding="large">
                <div className="text-center">
                  <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">📈</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Coverage Rate</h4>
                  <h2 className="text-4xl font-bold text-blue-600 mb-2">96%</h2>
                  <p className="text-gray-600">This week</p>
                </div>
              </Card>
              <Card className="h-full" hover padding="large">
                <div className="text-center">
                  <div className="bg-blue-50 rounded-full p-3 inline-block mb-3">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">✅</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Completed</h4>
                  <h2 className="text-4xl font-bold text-blue-600 mb-2">156</h2>
                  <p className="text-gray-600">This month</p>
                </div>
              </Card>
            </div>
          </Card>
        </div>

        {/* Form Elements - showcases InputField component */}
        <div className="mb-6">
          <Card padding="large" hover>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Form Elements</h3>
            <p className="text-gray-600 mb-6">Input fields and form components</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <InputField label="Email Address" type="email" name="demoEmail" placeholder="Enter your email" />
                <InputField label="Password" type="password" name="demoPassword" placeholder="Enter your password" />
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select Option</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
                    <option>Choose an option</option>
                    <option>Option 1</option>
                    <option>Option 2</option>
                  </select>
                </div>
              </div>
              <div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                  <textarea className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors" rows="4" placeholder="Enter your message"></textarea>
                </div>
                <div className="mb-4">
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-3 text-blue-600 focus:ring-blue-500" />
                    <span className="text-sm font-medium text-gray-900">Remember me</span>
                  </label>
                </div>
                <div>
                  <label className="flex items-center">
                    <input type="radio" name="radio1" className="mr-3 text-blue-600 focus:ring-blue-500" />
                    <span className="text-sm font-medium text-gray-900">Option 1</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <Button variant="primary">Save Changes</Button>
              <Button variant="success">Cancel</Button>
              <Button variant="danger">Reset</Button>
            </div>
          </Card>
        </div>

        {/* Color Palette */}
        <div className="mb-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Color Palette</h3>
            <p className="text-gray-600 mb-6">Blue theme colors and variations</p>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="bg-blue-600 rounded-2xl p-4 text-center text-white">
                <strong>Primary</strong>
                <br />
                <small>#2563eb</small>
              </div>
              <div className="bg-blue-50 rounded-2xl p-4 text-center">
                <strong>Light</strong>
                <br />
                <small>#eff6ff</small>
              </div>
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-4 text-center text-white">
                <strong>Gradient</strong>
                <br />
                <small>Blue mix</small>
              </div>
              <div className="border-2 border-blue-600 rounded-2xl p-4 text-center">
                <strong>Outline</strong>
                <br />
                <small>Border only</small>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl p-4 text-center">
                <strong>White</strong>
                <br />
                <small>#ffffff</small>
              </div>
              <div className="bg-gray-500 rounded-2xl p-4 text-center text-white">
                <strong>Muted</strong>
                <br />
                <small>#64748b</small>
              </div>
            </div>
          </div>
        </div>

        {/* Typography */}
        <div className="mb-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Typography</h3>
            <p className="text-gray-600 mb-6">Text styles and hierarchy</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h1 className="text-6xl font-bold text-blue-600 mb-2">Display 1</h1>
                <h2 className="text-5xl font-bold text-blue-600 mb-2">Display 2</h2>
                <h3 className="text-4xl font-bold text-blue-600 mb-2">Display 3</h3>
                <h4 className="text-3xl font-bold text-blue-600 mb-2">Display 4</h4>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Heading 1</h1>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Heading 2</h2>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Heading 3</h3>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Heading 4</h4>
                <h5 className="text-base font-bold text-gray-900 mb-2">Heading 5</h5>
                <h6 className="text-sm font-bold text-gray-900 mb-2">Heading 6</h6>
                <p className="text-lg text-gray-700 mb-2">This is a lead paragraph with larger text.</p>
                <p className="text-base text-gray-700 mb-2">This is a regular paragraph with normal text size.</p>
                <p className="text-sm text-gray-500">This is muted text for secondary information.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Elements */}
        <div className="mb-6">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Interactive Elements</h3>
            <p className="text-gray-600 mb-6">Hover effects and animations</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-2xl shadow-lg p-6 text-center hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="text-4xl mb-3">✨</div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Hover Card</h4>
                <p className="text-gray-600">This card lifts on hover</p>
              </div>
              <div className="text-center">
                <Button variant="primary" size="large" className="mb-2">
                  Hover Me
                </Button>
                <p className="text-gray-500">Button with hover effects</p>
              </div>
              <div className="bg-blue-50 rounded-2xl p-6 text-center hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="text-4xl mb-3">✨</div>
                <h5 className="text-lg font-semibold text-gray-900 mb-2">Lift Effect</h5>
                <p className="text-gray-600">This element lifts on hover</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
