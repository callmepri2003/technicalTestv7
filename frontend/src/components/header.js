// src/components/header.js
import { isAuthenticated, logout } from '../utils/authUtils';

export function renderHeader(targetElement, navigate) {
    const authenticated = isAuthenticated();
    targetElement.innerHTML = `
        <nav class="navbar">
            <div class="navbar-brand">
                <a href="#dashboard" class="logo">Budget Planner</a>
            </div>
            <ul class="navbar-menu">
                ${authenticated ? `
                    <li><a href="#dashboard">Dashboard</a></li>
                    <li><a href="#shopping-lists">Shopping Lists</a></li>
                    <li><a href="#transactions">Transactions</a></li>
                    <li><a href="#products">Products</a></li> <li><a href="#profile">Profile</a></li>
                    <li><button id="logout-btn" class="nav-button">Logout</button></li>
                ` : `
                    <li><a href="#login" class="nav-button">Login</a></li>
                `}
            </ul>
        </nav>
    `;

    if (authenticated) {
        document.getElementById('logout-btn').addEventListener('click', () => {
            logout();
            navigate('login');
        });
    }
}