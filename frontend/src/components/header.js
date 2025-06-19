// src/components/header.js
import { isAuthenticated, removeAuthToken } from '../utils/authUtils';

export function renderHeader(targetElement, navigate) {
    const loggedIn = isAuthenticated();
    targetElement.innerHTML = `
        <header class="header">
            <a href="#dashboard" class="logo">🛒 SmartList</a>
            <nav>
                <ul class="nav-list">
                    ${loggedIn ? `
                        <li><a href="#dashboard" class="nav-link">Dashboard</a></li>
                        <li><a href="#shopping-lists" class="nav-link">Shopping Lists</a></li>
                        <li><a href="#transactions" class="nav-link">Transactions</a></li>
                        <li><button id="logout-button" class="logout-button">Logout</button></li>
                    ` : `
                        <li><a href="#login" class="nav-link">Login</a></li>
                    `}
                </ul>
            </nav>
        </header>
    `;

    if (loggedIn) {
        const logoutButton = targetElement.querySelector('#logout-button');
        logoutButton.addEventListener('click', () => {
            removeAuthToken();
            navigate('login');
            renderHeader(targetElement, navigate); // Re-render header after logout
        });
    }
}