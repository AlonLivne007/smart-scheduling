/**
 * NotFound Page Component (404 Error)
 * 
 * The 404 error page that displays when a user navigates to a non-existent route.
 * Provides a user-friendly error message and navigation back to the home page.
 * 
 * Features:
 * - Clear error messaging
 * - Navigation back to home page
 * - Consistent styling with the rest of the application
 * - User-friendly design to reduce frustration
 * 
 * @component
 * @returns {JSX.Element} The 404 error page
 */
import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div>
      <h2>Page not found</h2>
      <p>The page you are looking for does not exist.</p>
      <Link to="/">Go home</Link>
    </div>
  )
}


