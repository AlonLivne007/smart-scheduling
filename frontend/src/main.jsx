/**
 * Application Entry Point
 * 
 * This is the main entry point for the React application. It initializes the app
 * and renders it to the DOM. Also imports all necessary CSS frameworks and styles.
 * 
 * Dependencies:
 * - React 18 with createRoot API for concurrent features
 * - Bootstrap CSS for layout and utility classes
 * - Bootstrap Icons for consistent iconography
 * - Custom CSS for blue theme and component styling
 * 
 * @fileoverview Main application entry point
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'bootstrap/dist/css/bootstrap.min.css'        // Bootstrap CSS framework
import 'bootstrap-icons/font/bootstrap-icons.css'   // Bootstrap Icons
import App from './App.jsx'                          // Main application component

// Create React root and render the application
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
