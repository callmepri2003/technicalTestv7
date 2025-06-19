// src/pages/dashboardPage.js
export function renderDashboardPage(targetElement, navigate) {
    targetElement.innerHTML = `
        <div class="container">
            <h1 class="heading">Welcome to SmartList!</h1>
            <p style="text-align: center; font-size: 1.1em; color: #666; margin-bottom: 40px;">Manage your shopping lists and transactions with ease.</p>
            <div class="card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
                <div class="card" id="card-shopping-lists" style="cursor: pointer;">
                    <h3 class="card-title">Shopping Lists</h3>
                    <p class="card-text">View and manage your predicted and actual shopping lists.</p>
                    <button class="card-button">Go to Lists</button>
                </div>
                <div class="card" id="card-transactions" style="cursor: pointer;">
                    <h3 class="card-title">Transactions</h3>
                    <p class="card-text">Keep track of your past purchases.</p>
                    <button class="card-button">Go to Transactions</button>
                </div>
            </div>
        </div>
    `;

    targetElement.querySelector('#card-shopping-lists').addEventListener('click', () => {
        navigate('shopping-lists');
    });

    targetElement.querySelector('#card-transactions').addEventListener('click', () => {
        navigate('transactions');
    });
}