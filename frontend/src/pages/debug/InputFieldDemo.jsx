/**
 * InputField Validation Demo Page
 * 
 * Demonstrates all the validation features of the enhanced InputField component.
 * This page showcases:
 * - Email validation
 * - Min/max length validation
 * - Pattern matching
 * - Custom validators
 * - Success states
 * - Error states
 * - Disabled/readonly states
 * 
 * @component
 */
import { useState } from 'react';
import InputField, { validators } from '../../components/ui/InputField.jsx';
import Button from '../../components/ui/Button.jsx';
import Card from '../../components/ui/Card.jsx';
import PageLayout from '../../layouts/PageLayout.jsx';
import { showSuccess, showError } from '../../lib/notifications.jsx';

export default function InputFieldDemo() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [age, setAge] = useState('');
  const [website, setWebsite] = useState('');
  const [phone, setPhone] = useState('');
  const [bio, setBio] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Check if all fields are valid (simplified - you'd do proper validation)
    if (!email || !username || !password) {
      showError('Please fill in all required fields');
      return;
    }
    
    showSuccess('Form validation passed! ✓');
    console.log({ email, username, password, age, website, phone, bio });
  };

  const handleReset = () => {
    setEmail('');
    setUsername('');
    setPassword('');
    setAge('');
    setWebsite('');
    setPhone('');
    setBio('');
    showSuccess('Form reset');
  };

  return (
    <PageLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            InputField Validation Demo
          </h1>
          <p className="text-gray-600">
            US-008: Enhanced InputField with real-time validation, visual feedback, and accessibility
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Form */}
          <div>
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Registration Form
              </h2>
              <form onSubmit={handleSubmit}>
                {/* Email with validation */}
                <InputField
                  label="Email Address"
                  type="email"
                  placeholder="john@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  validators={[
                    validators.required('Email is required'),
                    validators.email(),
                  ]}
                  showSuccess
                  required
                  helperText="We'll never share your email"
                />

                {/* Username with min/max length */}
                <InputField
                  label="Username"
                  placeholder="johndoe123"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  validators={[
                    validators.required('Username is required'),
                    validators.minLength(3, 'Username must be at least 3 characters'),
                    validators.maxLength(20, 'Username must be less than 20 characters'),
                    validators.pattern(/^[a-zA-Z0-9_]+$/, 'Only letters, numbers, and underscores allowed'),
                  ]}
                  showSuccess
                  required
                  helperText="3-20 characters, alphanumeric only"
                />

                {/* Password with custom validation */}
                <InputField
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  validators={[
                    validators.required('Password is required'),
                    validators.minLength(8, 'Password must be at least 8 characters'),
                    (value) => {
                      if (!/[A-Z]/.test(value)) return 'Must contain at least one uppercase letter';
                      if (!/[a-z]/.test(value)) return 'Must contain at least one lowercase letter';
                      if (!/[0-9]/.test(value)) return 'Must contain at least one number';
                      return null;
                    },
                  ]}
                  showSuccess
                  required
                  helperText="Min 8 chars with uppercase, lowercase, and number"
                />

                {/* Age with number validation */}
                <InputField
                  label="Age"
                  type="number"
                  placeholder="18"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  validators={[
                    validators.required('Age is required'),
                    validators.number(),
                    validators.min(18, 'Must be at least 18 years old'),
                    validators.max(120, 'Please enter a valid age'),
                  ]}
                  showSuccess
                  required
                />

                {/* Website with pattern validation */}
                <InputField
                  label="Website"
                  type="url"
                  placeholder="https://example.com"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  validators={[
                    validators.pattern(
                      /^https?:\/\/.+/,
                      'Must be a valid URL starting with http:// or https://'
                    ),
                  ]}
                  showSuccess
                  helperText="Optional - Your personal website"
                />

                {/* Phone with custom pattern */}
                <InputField
                  label="Phone Number"
                  type="tel"
                  placeholder="(555) 123-4567"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  validators={[
                    validators.pattern(
                      /^\(\d{3}\)\s\d{3}-\d{4}$/,
                      'Format: (555) 123-4567'
                    ),
                  ]}
                  showSuccess
                  helperText="Optional - Format: (555) 123-4567"
                />

                {/* Bio with max length */}
                <InputField
                  label="Bio"
                  placeholder="Tell us about yourself..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  validators={[
                    validators.maxLength(200, 'Bio must be less than 200 characters'),
                  ]}
                  showSuccess
                  helperText={`${bio.length}/200 characters`}
                />

                <div className="flex gap-3 mt-6">
                  <Button type="submit" variant="primary">
                    Submit Form
                  </Button>
                  <Button type="button" variant="outline" onClick={handleReset}>
                    Reset
                  </Button>
                </div>
              </form>
            </Card>
          </div>

          {/* Right Column - States Demo */}
          <div className="space-y-6">
            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Field States
              </h2>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Default State</h3>
                  <InputField
                    label="Normal Field"
                    placeholder="Type something..."
                    value=""
                    onChange={() => {}}
                  />
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Error State</h3>
                  <InputField
                    label="Field with Error"
                    placeholder="Invalid input"
                    value="bad@"
                    onChange={() => {}}
                    error="Invalid email format"
                  />
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Success State</h3>
                  <InputField
                    label="Valid Field"
                    placeholder="Valid input"
                    value="good@example.com"
                    onChange={() => {}}
                    validators={[validators.email()]}
                    showSuccess
                  />
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Disabled State</h3>
                  <InputField
                    label="Disabled Field"
                    placeholder="Cannot edit"
                    value="Read only value"
                    onChange={() => {}}
                    disabled
                  />
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Read-Only State</h3>
                  <InputField
                    label="Read-Only Field"
                    placeholder="Cannot edit"
                    value="Fixed value"
                    onChange={() => {}}
                    readOnly
                  />
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Features Checklist
              </h2>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Validation errors in red text below field</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Error appears after field is touched/blurred</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Error clears when typing correct value</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Red border on invalid field</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Green border on valid field (with showSuccess)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Built-in validators: email, min/max length, pattern</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Custom validation rules via functions</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Disabled and read-only states</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Helper text support</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>Icon indicators (checkmark/error)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 font-bold">✓</span>
                  <span>ARIA accessibility attributes</span>
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
