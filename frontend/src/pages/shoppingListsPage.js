// src/pages/shoppingListsPage.js
import { getShoppingLists } from '../api/shoppingList';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderShoppingListsPage(targetElement, navigate) { // Pass navigate to use it
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
                            ${list.completed_at ? `<p><strong>Completed:</strong> ${completedDate}</p>` : ''}
                            <button class="card-button view-details-btn" data-id="${list.id}">View Details</button>
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

            // NEW: Add event listeners for "View Details" buttons
            targetElement.querySelectorAll('.view-details-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const id = e.target.dataset.id;
                    if (id) {
                        navigate(`shopping-lists/${id}`);
                    }
                });
            });

        } else {
            targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${response.message}</p></div>`;
        }
    } catch (error) {
        removeLoadingSpinner(targetElement);
        const errorMessage = error.response?.data?.message || 'Failed to fetch shopping lists.';
        targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${errorMessage}</p></div>`;
    }
}