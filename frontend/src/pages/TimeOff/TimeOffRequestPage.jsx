import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import InputField from '../../components/ui/InputField';
import Button from '../../components/ui/Button';
import { createTimeOffRequest } from '../../api/timeOff';
import { validators } from '../../components/ui/InputField';

export default function TimeOffRequestPage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    request_type: 'VACATION'
  });
  const [errors, setErrors] = useState({});

  const requestTypes = [
    { value: 'VACATION', label: 'Vacation' },
    { value: 'SICK', label: 'Sick Leave' },
    { value: 'PERSONAL', label: 'Personal' },
    { value: 'OTHER', label: 'Other' }
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    const today = new Date().toISOString().split('T')[0];

    // Required fields
    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    } else if (formData.start_date < today) {
      newErrors.start_date = 'Start date must be in the future';
    }

    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    } else if (formData.end_date < formData.start_date) {
      newErrors.end_date = 'End date must be after start date';
    }

    if (!formData.request_type) {
      newErrors.request_type = 'Request type is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }

    setIsSubmitting(true);

    try {
      await createTimeOffRequest(formData);
      toast.success('Time-off request submitted successfully!');
      
      // Clear form
      setFormData({
        start_date: '',
        end_date: '',
        request_type: 'VACATION'
      });

      // Navigate to my requests page after a short delay
      setTimeout(() => {
        navigate('/time-off/my-requests');
      }, 1500);
    } catch (error) {
      console.error('Failed to create time-off request:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate(-1); // Go back to previous page
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Request Time Off</h1>
        <p className="text-gray-600 mt-1">Submit a request for vacation, sick leave, or personal time off</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Request Type */}
          <div>
            <label htmlFor="request_type" className="block text-sm font-medium text-gray-700 mb-2">
              Request Type <span className="text-red-500">*</span>
            </label>
            <select
              id="request_type"
              name="request_type"
              value={formData.request_type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {requestTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            {errors.request_type && (
              <p className="mt-1 text-sm text-red-600">{errors.request_type}</p>
            )}
          </div>

          {/* Start Date */}
          <div>
            <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-2">
              Start Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
              min={new Date().toISOString().split('T')[0]}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.start_date ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.start_date && (
              <p className="mt-1 text-sm text-red-600">{errors.start_date}</p>
            )}
          </div>

          {/* End Date */}
          <div>
            <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-2">
              End Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              id="end_date"
              name="end_date"
              value={formData.end_date}
              onChange={handleChange}
              min={formData.start_date || new Date().toISOString().split('T')[0]}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.end_date ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.end_date && (
              <p className="mt-1 text-sm text-red-600">{errors.end_date}</p>
            )}
          </div>

          {/* Info Box */}
          {formData.start_date && formData.end_date && formData.end_date >= formData.start_date && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-blue-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="text-sm text-blue-700">
                  <p className="font-medium">Request Summary</p>
                  <p className="mt-1">
                    Requesting {Math.ceil((new Date(formData.end_date) - new Date(formData.start_date)) / (1000 * 60 * 60 * 24)) + 1} day(s) off
                    from {new Date(formData.start_date).toLocaleDateString()} to {new Date(formData.end_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              isLoading={isSubmitting}
              className="flex-1"
            >
              Submit Request
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>

      {/* Help Text */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Need to know:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Your manager will be notified of your request</li>
          <li>• You'll receive a notification when your request is approved or rejected</li>
          <li>• You can view all your requests in "My Time-Off" page</li>
          <li>• Pending requests can be edited or cancelled</li>
        </ul>
      </div>
    </div>
  );
}
