// src/pages/dashboardPage.js
import { generateShoppingLists } from '../api/shoppingList';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export function renderDashboardPage(targetElement, navigate) {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const defaultStartDate = `${year}-${month}-${day}`;

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
                <div class="card" id="card-generate-list" style="cursor: pointer;">
                    <h3 class="card-title">Generate New List</h3>
                    <p class="card-text">Predict and create a new shopping list based on your history.</p>
                    <button class="card-button">Generate List</button>
                </div>
            </div>

            <div id="generate-list-form-container" class="hidden-form-container">
                <h2 class="heading">Generate Shopping List</h2>
                <form id="generate-list-form" class="form">
                    <div class="input-group">
                        <label for="num_lists" class="label">Number of Lists to Generate:</label>
                        <input type="number" id="num_lists" class="input" value="1" min="1" required>
                    </div>
                    <div class="input-group">
                        <label for="start_date" class="label">Start Date:</label>
                        <input type="date" id="start_date" class="input" value="${defaultStartDate}" required>
                    </div>
                    <button type="submit" class="button">Generate</button>
                    <button type="button" id="cancel-generate" class="button button-secondary">Cancel</button>
                    <p id="generate-message" class="message"></p>
                </form>
            </div>
        </div>
    `;

    // Event Listeners
    targetElement.querySelector('#card-shopping-lists').addEventListener('click', () => {
        navigate('shopping-lists');
    });

    targetElement.querySelector('#card-transactions').addEventListener('click', () => {
        navigate('transactions');
    });

    const generateListCard = targetElement.querySelector('#card-generate-list');
    const generateListFormContainer = targetElement.querySelector('#generate-list-form-container');
    const generateListForm = targetElement.querySelector('#generate-list-form');
    const generateMessage = targetElement.querySelector('#generate-message');
    const cancelButton = targetElement.querySelector('#cancel-generate');

    generateListCard.addEventListener('click', () => {
        generateListFormContainer.classList.remove('hidden-form-container');
        generateListCard.style.display = 'none'; // Hide the card when form is shown
    });

    cancelButton.addEventListener('click', () => {
        generateListFormContainer.classList.add('hidden-form-container');
        generateListCard.style.display = 'flex'; // Show the card again
        generateMessage.textContent = ''; // Clear any messages
        generateMessage.className = 'message';
    });

    generateListForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        renderLoadingSpinner(targetElement); // Show spinner while generating

        const numLists = generateListForm.querySelector('#num_lists').value;
        const startDate = generateListForm.querySelector('#start_date').value;

        generateMessage.textContent = '';
        generateMessage.className = 'message'; // Reset classes

        try {
            const response = await generateShoppingLists({
                num_lists: parseInt(numLists),
                start_date: startDate
            });
            removeLoadingSpinner(targetElement); // Remove spinner on success/failure

            if (response.success) {
                generateMessage.textContent = response.message || 'Shopping list(s) generated successfully!';
                generateMessage.classList.add('success');
                // Optionally navigate to shopping lists page after a short delay
                setTimeout(() => {
                    navigate('shopping-lists');
                }, 1500);
            } else {
                generateMessage.textContent = response.message || 'Failed to generate shopping list(s).';
                generateMessage.classList.add('error');
            }
        } catch (error) {
            removeLoadingSpinner(targetElement); // Remove spinner on error
            console.error('Error generating list:', error);
            generateMessage.textContent = error.response?.data?.message || 'An unexpected error occurred.';
            generateMessage.classList.add('error');
        }
    });
}