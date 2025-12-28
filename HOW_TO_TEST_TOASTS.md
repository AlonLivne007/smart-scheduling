# How to Test the Toast Notifications Implementation

## Current Status
✅ Frontend dev server is running on **http://localhost:5173**  
✅ Toast notifications system is fully implemented

## What You'll See

### 1. Login Page (First Load)
- The app requires authentication
- You'll see a login form with email/password fields
- **Status:** Backend is not currently running, so login won't work

### 2. To See Toast Notifications in Action

You have two options:

#### Option A: Mock the Auth Locally (Recommended for Quick Testing)
1. Open browser DevTools (F12)
2. Go to Console tab
3. Run these commands:
```javascript
// Simulate a logged-in user
localStorage.setItem('access_token', 'mock-token-for-testing')
localStorage.setItem('auth_user', JSON.stringify({
  user_id: 1,
  user_full_name: 'Test User',
  user_email: 'test@example.com',
  is_manager: true,
  roles: []
}))

// Refresh the page
location.reload()
```

4. You should now see the Dashboard with a welcome toast notification ✓

#### Option B: Run the Full Backend Stack with Docker
1. Install Docker Desktop
2. Run: `docker compose up --build` from the project root
3. This will start:
   - Backend API (port 8000)
   - Frontend (port 5173)
   - PostgreSQL Database (port 5432)
4. Login with test credentials (if seed data is available)

---

## Testing Toast Notifications After Login

### 1. Welcome Toast (Automatic)
- When you first load the Dashboard, you'll see:
```
✓ Welcome back! Dashboard loaded successfully.
```
(Green toast, auto-dismisses after 4 seconds)

### 2. Demo Section (Manual Testing)
1. Navigate to **Settings** (left sidebar)
2. Scroll to the **blue highlighted section**: "Toast Notifications Demo"
3. Click any of the 5 test buttons:

| Button | Toast Type | Color | Duration |
|--------|-----------|-------|----------|
| ✓ Success | Success | Green | 4s |
| ✗ Error | Error | Red | 5s |
| ℹ Info | Info | Blue | 4s |
| ⚠ Warning | Warning | Yellow | 5s |
| ⏳ Loading | Loading | Blue | Manual |

### 3. Interactive Features to Test
- **Stack Multiple**: Click multiple buttons quickly to see toasts stack vertically
- **Dismiss**: Click the X button on any toast to manually dismiss it
- **Auto-Dismiss**: Watch toasts disappear automatically after their duration
- **Loading Toast**: Click the Loading button and watch it show for 2 seconds, then dismiss and show success

---

## What Was Implemented

### Files Modified:
1. **`src/lib/notifications.jsx`** ✨ NEW
   - Complete notification utility module
   - 8 functions for different notification types
   - Smart API error handling

2. **`src/layouts/MainLayout.jsx`** 📝 UPDATED
   - Added `<Toaster />` component
   - Configured styling for all notification types

3. **`src/pages/HomePage.jsx`** 📝 UPDATED
   - Integrated welcome toast on page load

4. **`src/pages/SettingsPage.jsx`** 📝 UPDATED
   - Added demo section with 5 test buttons

### Packages Added:
- `react-hot-toast` (lightweight toast library)

---

## Quick Test Without Backend

### Step-by-Step:

1. **Open the app**: http://localhost:5173
2. **Open DevTools**: Press F12
3. **Go to Console tab**
4. **Paste and run this code block:**

```javascript
// Mock user authentication
localStorage.setItem('access_token', 'mock-token')
localStorage.setItem('auth_user', JSON.stringify({
  user_id: 1,
  user_full_name: 'Test Manager',
  user_email: 'manager@company.com',
  is_manager: true,
  roles: [{ role_id: 1, role_name: 'Manager' }]
}))

// Refresh page
location.reload()
```

5. **Wait for page to reload**
6. You should see:
   - ✓ Welcome toast notification
   - Dashboard page with sidebar navigation
   - Settings link in sidebar

7. **Click Settings** in the sidebar
8. **Scroll down** to find "Toast Notifications Demo" section (blue background)
9. **Click the test buttons** to see different toast types

---

## Expected Results

### Success Toast
```
┌─────────────────────────────────────┐
│ ✓ Settings saved successfully!       │
│                                     X│
└─────────────────────────────────────┘
```
- Green background
- Auto-dismisses after 4 seconds
- Appears in top-right corner

### Error Toast  
```
┌─────────────────────────────────────┐
│ ✗ Failed to save settings.          │
│   Please try again.                 │
│                                     X│
└─────────────────────────────────────┘
```
- Red background
- Auto-dismisses after 5 seconds
- Appears in top-right corner

### Multiple Toasts Stacking
```
┌─────────────────────────┐
│ ✓ First notification    │ X │ (top)
├─────────────────────────┤
│ ✓ Second notification   │ X │ (middle)
├─────────────────────────┤
│ ✓ Third notification    │ X │ (bottom - newest)
└─────────────────────────┘
```
- All stack in top-right corner
- Spaced 8px apart
- Each independently dismissible

---

## Next Steps

Once you've verified the toast notifications work:

1. **US-002: Error Boundary** - Catch and display errors gracefully
2. **US-003: Loading Skeletons** - Show placeholders while loading data
3. **US-004: Loading Spinners** - Show spinner during page transitions
4. **US-005: Connect Dashboard to Backend** - Fetch real data and show metrics

These will all use the toast notification system we just built!

---

## Troubleshooting

### I see a blank page
- **Solution:** Make sure frontend dev server is running
- Check terminal output shows "VITE v7.1.9 ready in 370 ms"

### Toasts don't appear
- **Solution:** Try the DevTools mock auth code above
- Make sure you're on the Settings page to see demo buttons

### Backend doesn't work
- **Solution:** For now, just use the DevTools mock (see above)
- Full backend setup with Docker is optional for testing toasts

### Pages keep redirecting to login
- **Solution:** The auth check is working correctly
- Use DevTools console to mock auth (see Quick Test section)

---

## Documentation References

- **Full Implementation**: `IMPLEMENTATION_US-001_TOAST_NOTIFICATIONS.md`
- **Quick Reference**: `TOAST_NOTIFICATIONS_QUICK_REFERENCE.md`
- **React Hot Toast Docs**: https://react-hot-toast.com/

---

## Demo Commands for Console

Copy-paste any of these into DevTools Console to test:

```javascript
// Import the toast functions
const { showSuccess, showError, showInfo, showWarning, showLoading, dismissToast } = await import('/src/lib/notifications.jsx')

// Test each type
showSuccess('This is a success message')
showError('This is an error message')
showInfo('This is an info message')
showWarning('This is a warning message')
const toastId = showLoading('This is a loading message')
setTimeout(() => dismissToast(toastId), 2000)
```

---

## Summary

🎉 **Toast Notifications System is COMPLETE and READY!**

- ✅ All acceptance criteria met
- ✅ Fully styled and integrated
- ✅ Demo section for testing
- ✅ Ready for use in other features

**Next Story:** US-002: Error Boundary Component (5 story points)
