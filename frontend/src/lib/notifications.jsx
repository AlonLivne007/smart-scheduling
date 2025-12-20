/**
 * Notifications Utility
 * 
 * Provides helper functions for displaying toast notifications throughout the app.
 * Uses react-hot-toast for rendering non-intrusive toast messages.
 * 
 * @example
 * import { showSuccess, showError, showInfo, showWarning } from '@/lib/notifications'
 * 
 * // Success notification
 * showSuccess('User created successfully!')
 * 
 * // Error notification
 * showError('Failed to create user. Please try again.')
 * 
 * // Info notification
 * showInfo('Processing your request...')
 * 
 * // Warning notification
 * showWarning('This action cannot be undone.')
 */

import toast from 'react-hot-toast';

/**
 * Display a success notification
 * @param {string} message - The success message to display
 * @param {Object} options - Optional toast configuration
 * @returns {string} Toast ID
 */
export const showSuccess = (message, options = {}) => {
  return toast.success(message, {
    duration: 4000,
    position: 'top-right',
    ...options,
  });
};

/**
 * Display an error notification
 * @param {string} message - The error message to display
 * @param {Object} options - Optional toast configuration
 * @returns {string} Toast ID
 */
export const showError = (message, options = {}) => {
  return toast.error(message, {
    duration: 5000,
    position: 'top-right',
    ...options,
  });
};

/**
 * Display an info notification
 * @param {string} message - The info message to display
 * @param {Object} options - Optional toast configuration
 * @returns {string} Toast ID
 */
export const showInfo = (message, options = {}) => {
  return toast(message, {
    duration: 4000,
    position: 'top-right',
    ...options,
  });
};

/**
 * Display a warning notification
 * @param {string} message - The warning message to display
 * @param {Object} options - Optional toast configuration
 * @returns {string} Toast ID
 */
export const showWarning = (message, options = {}) => {
  return toast.custom(
    () => (
      <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-300 rounded-lg px-4 py-3">
        <span className="text-lg">⚠️</span>
        <span className="text-yellow-900">{message}</span>
      </div>
    ),
    {
      duration: 5000,
      position: 'top-right',
      ...options,
    }
  );
};

/**
 * Display a loading notification (doesn't auto-dismiss)
 * @param {string} message - The loading message to display
 * @returns {string} Toast ID (use this to dismiss later)
 */
export const showLoading = (message) => {
  return toast.loading(message, {
    position: 'top-right',
  });
};

/**
 * Dismiss a specific toast by ID
 * @param {string} toastId - The ID returned from a toast function
 */
export const dismissToast = (toastId) => {
  if (toastId) {
    toast.dismiss(toastId);
  }
};

/**
 * Dismiss all active toasts
 */
export const dismissAllToasts = () => {
  toast.remove();
};

/**
 * Display a promise-based toast (great for async operations)
 * Shows loading while promise is pending, then success or error
 * @param {Promise} promise - Promise to track
 * @param {Object} messages - Object with loading, success, and error messages
 * @returns {Promise}
 * 
 * @example
 * showPromise(
 *   fetchUsers(),
 *   {
 *     loading: 'Fetching users...',
 *     success: 'Users fetched!',
 *     error: 'Failed to fetch users'
 *   }
 * )
 */
export const showPromise = (promise, messages) => {
  return toast.promise(
    promise,
    {
      loading: messages.loading || 'Loading...',
      success: messages.success || 'Success!',
      error: messages.error || 'Error occurred',
    },
    {
      position: 'top-right',
    }
  );
};

/**
 * Custom hook to handle API errors and display appropriate toast
 * @param {Error} error - The error object
 * @returns {void}
 */
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.detail || error.response.data?.message || 'An error occurred';
    
    if (status === 401) {
      showError('Session expired. Please log in again.');
    } else if (status === 403) {
      showError('You do not have permission to perform this action.');
    } else if (status === 404) {
      showError('The requested resource was not found.');
    } else if (status === 422) {
      showError(`Validation error: ${message}`);
    } else if (status >= 500) {
      showError('Server error. Please try again later.');
    } else {
      showError(message);
    }
  } else if (error.request) {
    // Request made but no response
    showError('Network error. Please check your connection.');
  } else {
    // Error in request setup
    showError(error.message || 'An unexpected error occurred.');
  }
};

export default {
  showSuccess,
  showError,
  showInfo,
  showWarning,
  showLoading,
  showPromise,
  dismissToast,
  dismissAllToasts,
  handleApiError,
};
