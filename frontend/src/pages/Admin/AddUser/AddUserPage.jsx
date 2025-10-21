/**
 * AddUserPage Component
 * 
 * Main container component for the admin add user page that orchestrates all sub-components.
 * Manages the overall layout, form state, validation, and coordinates between child components.
 * 
 * Features:
 * - Soft blue-to-white gradient background
 * - Centered form card with shadow
 * - Modular component structure for maintainability
 * - Form validation with error handling
 * - Admin-focused user creation workflow
 * 
 * @component
 * @returns {JSX.Element} The complete add user admin page
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AddUserHeader from './AddUserHeader.jsx';
import AddUserForm from './AddUserForm.jsx';
import AddUserActions from './AddUserActions.jsx';
import PageLayout from '../../../layouts/PageLayout.jsx';
import Card from '../../../components/ui/Card.jsx';

export default function AddUserPage() {
  const navigate = useNavigate();
  
  // Form state management
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    role: '',
    is_manager: false
  });

  // Error state management
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Handles input field changes and updates form state
   * Clears validation errors when user starts typing
   * @param {Event} e - Input change event
   */
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  /**
   * Validates the add user form and sets error messages
   * @returns {boolean} True if form is valid, false otherwise
   */
  const validateForm = () => {
    const newErrors = {};

    // Full name validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 2) {
      newErrors.fullName = 'Full name must be at least 2 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    // Role validation
    if (!formData.role) {
      newErrors.role = 'Role is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handles form submission for user creation
   * Validates form before processing
   * @param {Event} e - Form submit event
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      handleCreateUser();
    }
  };

  /**
   * Handles the create user action
   * Simulates API call and navigation
   */
  const handleCreateUser = async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Handle user creation logic here
      console.log('Creating user with data:', {
        user_full_name: formData.fullName,
        user_email: formData.email,
        user_hashed_password: formData.password, // This would be hashed on backend
        is_manager: formData.is_manager,
        role: formData.role
      });
      
      // Navigate back to admin dashboard or users list
      navigate('/admin/users');
    } catch (error) {
      console.error('Error creating user:', error);
      // Handle error (show notification, etc.)
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles cancel action
   * Navigates back to previous page or admin dashboard
   */
  const handleCancel = () => {
    navigate(-1); // Go back to previous page
  };

  return (
    <PageLayout>
      <div className="w-full max-w-2xl mx-auto">
        {/* Header Section - Logo and Page Title */}
        <AddUserHeader />

        {/* Add User Card */}
        <Card padding="large" hover>
          {/* Add User Form */}
          <AddUserForm 
            formData={formData}
            errors={errors}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          />

          {/* Action Buttons */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <AddUserActions 
              onCreateUser={handleCreateUser}
              onCancel={handleCancel}
              isLoading={isLoading}
            />
          </div>
        </Card>
      </div>
    </PageLayout>
  );
}
