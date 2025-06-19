// src/main.js
import './style.css';
import { renderHeader } from './components/header';
import { renderLoginPage } from './pages/loginPage';
import { renderDashboardPage } from './pages/dashboardPage';
import { renderShoppingListsPage } from './pages/shoppingListsPage';
import { renderShoppingListDetailPage } from './pages/shoppingListDetailPage';
import { renderTransactionsPage } from './pages/transactionsPage';
import { renderTransactionDetailPage } from './pages/transactionDetailPage';
import { renderUserProfilePage } from './pages/userProfilePage';
import { renderProductsPage } from './pages/productsPage';
import { renderUploadTransactionsPage } from './pages/uploadTransactionsPage'; // NEW IMPORT
import { isAuthenticated } from './utils/authUtils';

const appHeader = document.getElementById('app-header');
const appContent = document.getElementById('app-content');

const renderPage = async (path) => {
  appContent.innerHTML = '';

  const pathParts = path.split('/');
  const baseRoute = pathParts[0];
  const id = pathParts[1];

  const authRequiredRoutes = ['dashboard', 'shopping-lists', 'transactions', 'profile', 'products', 'upload-transactions']; // Add 'upload-transactions'
  if (authRequiredRoutes.includes(baseRoute) && !isAuthenticated()) {
    window.location.hash = '#login';
    return;
  }

  switch (baseRoute) {
    case 'login':
      renderLoginPage(appContent, navigate, () => renderHeader(appHeader, navigate));
      break;
    case 'dashboard':
      renderDashboardPage(appContent, navigate);
      break;
    case 'shopping-lists':
      if (id) {
        await renderShoppingListDetailPage(appContent, id);
      } else {
        await renderShoppingListsPage(appContent, navigate);
      }
      break;
    case 'transactions':
      if (id) {
        await renderTransactionDetailPage(appContent, id);
      } else {
        await renderTransactionsPage(appContent, navigate);
      }
      break;
    case 'profile':
      await renderUserProfilePage(appContent);
      break;
    case 'products':
      if (id) {
        await renderProductDetailPage(appContent, id);
      } else {
        await renderProductsPage(appContent, navigate);
      }
      break;
    case 'upload-transactions': // NEW ROUTE
        await renderUploadTransactionsPage(appContent, navigate);
        break;
    case '':
      window.location.hash = '#dashboard';
      break;
    default:
      appContent.innerHTML = '<div class="container"><h1 class="heading">404 Not Found</h1><p class="message error">The page you are looking for does not exist.</p></div>';
      break;
  }
};

const navigate = (path) => {
  window.location.hash = `#${path}`;
};

const handleRouteChange = () => {
  const path = window.location.hash.substring(1) || '';
  renderHeader(appHeader, navigate); // Always render header based on current auth state
  renderPage(path);
};

window.addEventListener('hashchange', handleRouteChange);
handleRouteChange();