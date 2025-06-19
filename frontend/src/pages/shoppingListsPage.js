// src/pages/shoppingListsPage.js
import { getShoppingLists } from '../api/shoppingList';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderShoppingListsPage(targetElement) {
    renderLoadingSpinner(targetElement);

    try {
        const response = await getShoppingLists();
        removeLoadingSpinner(targetElement);

        if (response.success) {
            const lists = response.data.results;
            let listHtml = '';
            if (lists.length === 0) {
                listHtml = '<p class="no-data-message">No shopping lists found. Start generating one from the dashboard!</p>';
            } else {
                listHtml = lists.map(list => {
                    const statusClass = `status-${list.status.toLowerCase().replace('_', '-')}`;
                    const completedDate = list.completed_at ? new Date(list.completed_at).toLocaleDateString() : 'N/A';
                    return `
                        <div class="card">
                            <h3 class="card-title">List #${list.id}</h3>
                            <p><strong>Scheduled Date:</strong> ${list.scheduled_date}</p>
                            <p><strong>Status:</strong> <span class="${statusClass}">${list.status.replace('_', ' ')}</span></p>
                            <p><strong>Created:</strong> ${new Date(list.created_at).toLocaleDateString()}</p>
                            <p><strong>Completed:</strong> ${completedDate}</p>
                            <button class="card-button">View Details</button>
                        </div>
                    `;
                }).join('');
                listHtml = `<div class="card-grid">${listHtml}</div>`;
            }

            targetElement.innerHTML = `
                <div class="container">
                    <h1 class="heading">Your Shopping Lists</h1>
                    ${listHtml}
                </div>
            `;
        } else {
            targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${response.message}</p></div>`;
        }
    } catch (error) {
        removeLoadingSpinner(targetElement);
        const errorMessage = error.response?.data?.message || 'Failed to fetch shopping lists.';
        targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${errorMessage}</p></div>`;
    }
}