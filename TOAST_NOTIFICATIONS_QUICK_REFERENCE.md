# Toast Notifications Quick Reference

## Installation ✅ 
Already installed: `npm install react-hot-toast`

## Setup ✅
Already configured in `src/layouts/MainLayout.jsx`

---

## Basic Usage

### Import
```jsx
import { showSuccess, showError, showInfo, showWarning, showLoading, dismissToast } from '@/lib/notifications.jsx'
```

### Simple Notifications
```jsx
// Success (green, 4s auto-dismiss)
showSuccess('Operation completed!')

// Error (red, 5s auto-dismiss)  
showError('Something went wrong!')

// Info (blue, 4s auto-dismiss)
showInfo('Here is some information')

// Warning (yellow, 5s auto-dismiss)
showWarning('This action cannot be undone')
```

---

## Advanced Usage

### Loading State (Manual Dismiss)
```jsx
const handleLongOperation = async () => {
  const toastId = showLoading('Processing...')
  
  try {
    await longOperation()
    dismissToast(toastId)  // Remove loading toast
    showSuccess('Done!')
  } catch (error) {
    dismissToast(toastId)
    showError('Failed!')
  }
}
```

### Promise-Based (Auto-Handle States)
```jsx
showPromise(
  fetchData(),
  {
    loading: 'Loading data...',
    success: 'Data loaded!',
    error: 'Failed to load data'
  }
)
```

### Smart API Error Handling
```jsx
import { handleApiError } from '@/lib/notifications.jsx'

const handleCreateUser = async () => {
  try {
    await api.post('/users', data)
    showSuccess('User created!')
  } catch (error) {
    handleApiError(error)  // Auto-detects error type
  }
}
```

---

## Common Scenarios

### Form Submission
```jsx
const handleSubmit = async (formData) => {
  const toastId = showLoading('Saving...')
  try {
    await api.post('/data', formData)
    dismissToast(toastId)
    showSuccess('Saved successfully!')
    // Navigate or reset form
  } catch (error) {
    dismissToast(toastId)
    handleApiError(error)
  }
}
```

### Delete Confirmation
```jsx
const handleDelete = async (id) => {
  if (!confirm('Are you sure?')) return
  
  const toastId = showLoading('Deleting...')
  try {
    await api.delete(`/resource/${id}`)
    dismissToast(toastId)
    showSuccess('Deleted!')
  } catch (error) {
    dismissToast(toastId)
    showError('Failed to delete')
  }
}
```

### Validation Errors
```jsx
const handleFormValidation = (errors) => {
  if (errors.length > 0) {
    showError(`${errors.length} validation error(s)`)
  }
}
```

---

## Styling & Customization

### Override Default Duration
```jsx
showSuccess('Quick notification', { duration: 2000 })
showError('Sticky error', { duration: Infinity })
```

### Custom Options
```jsx
showSuccess('Message', {
  duration: 3000,
  position: 'bottom-center',  // 'top-left', 'top-center', 'top-right', 'bottom-left', etc
})
```

---

## Available Positions
- `top-left`
- `top-center`
- `top-right` (default)
- `bottom-left`
- `bottom-center`
- `bottom-right`

---

## Tips & Best Practices

✅ **DO:**
- Use `showLoading()` + `dismissToast()` for long operations
- Use `handleApiError()` for all API calls
- Show brief, actionable messages (< 100 characters ideally)
- Use appropriate notification type for the action
- Dismiss loading toast before showing result

❌ **DON'T:**
- Show multiple success notifications in a row
- Use error toast for info messages
- Keep loading toast visible indefinitely
- Show toasts in response to every action (reserve for important feedback)

---

## React Hot Toast Documentation
https://react-hot-toast.com/

---

## Example: Complete User Form
```jsx
import { showSuccess, showError, showLoading, dismissToast, handleApiError } from '@/lib/notifications.jsx'
import axios from 'axios'
import { useState } from 'react'

export default function UserForm() {
  const [formData, setFormData] = useState({ name: '', email: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (!formData.name || !formData.email) {
      showError('Name and email are required')
      return
    }

    // Show loading
    const toastId = showLoading('Creating user...')

    try {
      const response = await axios.post('/api/users', formData)
      dismissToast(toastId)
      showSuccess('User created successfully!')
      setFormData({ name: '', email: '' })  // Reset form
    } catch (error) {
      dismissToast(toastId)
      handleApiError(error)  // Smart error handling
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        placeholder="Name"
      />
      <input 
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        placeholder="Email"
      />
      <button type="submit">Create User</button>
    </form>
  )
}
```

---

## Testing Toasts

Navigate to **Settings Page** → "Toast Notifications Demo" section to test all notification types with demo buttons.
