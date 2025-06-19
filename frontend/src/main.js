// src/main.js
import './style.css'; // Import global styles
import { renderHeader } from './components/header';
import { renderLoginPage } from './pages/loginPage';
import { renderDashboardPage } from './pages/dashboardPage';
import { renderShoppingListsPage } from './pages/shoppingListsPage';
import { renderTransactionsPage } from './pages/transactionsPage';
import { isAuthenticated } from './utils/authUtils';

const appHeader = document.getElementById('app-header');
const appContent = document.getElementById('app-content');

// Function to clear content and render a page
const renderPage = async (path) => {
  appContent.innerHTML = ''; // Clear previous content

  // Check authentication for protected routes
  const authRequiredRoutes = ['dashboard', 'shopping-lists', 'transactions'];
  const currentRoute = path.split('/')[0]; // Get the base route (e.g., 'dashboard' from 'dashboard/123')

  if (authRequiredRoutes.includes(currentRoute) && !isAuthenticated()) {
    window.location.hash = '#login'; // Redirect to login if not authenticated
    return;
  }

  switch (currentRoute) {
    case 'login':
      renderLoginPage(appContent, navigate, () => renderHeader(appHeader, navigate));
      break;
    case 'dashboard':
      renderDashboardPage(appContent, navigate);
      break;
    case 'shopping-lists':
      await renderShoppingListsPage(appContent);
      break;
    case 'transactions':
      await renderTransactionsPage(appContent);
      break;
    case '': // Default route (e.g., when visiting just '/')
      window.location.hash = '#dashboard';
      break;
    default:
      appContent.innerHTML = '<div class="container"><h1 class="heading">404 Not Found</h1><p class="message error">The page you are looking for does not exist.</p></div>';
      break;
  }
};

// Simple hash-based router
const navigate = (path) => {
  window.location.hash = `#${path}`;
};

// Handle initial load and hash changes
const handleRouteChange = () => {
  const path = window.location.hash.substring(1) || ''; // Remove '#' and get path
  renderHeader(appHeader, navigate); // Always render header based on current auth state
  renderPage(path);
};

// Listen for hash changes
window.addEventListener('hashchange', handleRouteChange);

// Initial route render
handleRouteChange();