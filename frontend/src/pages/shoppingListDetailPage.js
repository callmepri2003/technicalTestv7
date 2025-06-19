// src/pages/shoppingListDetailPage.js
import {
    getShoppingListDetail,
    updateShoppingList,
    deleteShoppingList,
    completeShoppingList,
    convertExpiredToTransaction
} from '../api/shoppingList';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderShoppingListDetailPage(targetElement, id) {
    let currentShoppingList = null; // Store the fetched list for various actions

    const fetchAndRenderList = async () => {
        renderLoadingSpinner(targetElement);
        try {
            const response = await getShoppingListDetail(id);
            removeLoadingSpinner(targetElement);

            if (response.success) {
                currentShoppingList = response.data; // Store the list data
                const list = currentShoppingList;
                const statusClass = `status-${list.status.toLowerCase().replace('_', '-')}`;
                const completedDate = list.completed_at ? new Date(list.completed_at).toLocaleDateString() : 'N/A';

                let itemsHtml = '';
                if (list.items && list.items.length > 0) {
                    itemsHtml = `
                        <h3>Items:</h3>
                        <div class="card-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                            ${list.items.map(item => `
                                <div class="card small-card shopping-list-item-card" data-item-id="${item.id}" data-product-id="${item.product.id}">
                                    <p><strong>Product:</strong> ${item.product.name}</p>
                                    <p><strong>Category:</strong> ${item.product.category || 'N/A'}</p>
                                    <p><strong>Predicted Qty:</strong> ${item.predicted_quantity} ${item.product.default_unit || 'item'}</p>
                                    <p><strong>Actual Qty:</strong> ${item.actual_quantity !== null ? `${item.actual_quantity} ${item.product.default_unit || 'item'}` : 'N/A'}</p>
                                    <p><strong>Purchased:</strong> ${item.is_purchased ? 'Yes' : 'No'}</p>
                                    ${list.status === 'IN_PROGRESS' ? `
                                        <div class="input-group" style="margin-top: 10px;">
                                            <label for="actual-qty-${item.id}" class="label" style="font-size: 0.85em; margin-bottom: 5px;">Update Actual Qty:</label>
                                            <input type="number" step="0.01" id="actual-qty-${item.id}" class="input small-input item-actual-qty"
                                                value="${item.actual_quantity !== null ? item.actual_quantity : item.predicted_quantity}"
                                                min="0">
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    itemsHtml = '<p class="no-data-message" style="margin-top: 15px;">No items in this list.</p>';
                }

                targetElement.innerHTML = `
                    <div class="container">
                        <h1 class="heading">Shopping List Details: #${list.id}</h1>
                        <div class="detail-section">
                            <p><strong>Scheduled Date:</strong> ${list.scheduled_date}</p>
                            <p><strong>Status:</strong> <span class="${statusClass}">${list.status.replace('_', ' ')}</span></p>
                            <p><strong>Created At:</strong> ${new Date(list.created_at).toLocaleString()}</p>
                            <p><strong>Last Updated:</strong> ${new Date(list.updated_at).toLocaleString()}</p>
                            <p><strong>Completed At:</strong> ${completedDate}</p>
                        </div>

                        <div class="section-controls" style="margin-bottom: 20px;">
                            ${list.status === 'IN_PROGRESS' ? `
                                <button id="finalize-list-btn" class="button">Finalize Shopping</button>
                                <button id="delete-list-btn" class="button button-danger">Delete List</button>
                            ` : ''}
                            ${list.status === 'EXPIRED' ? `
                                <button id="convert-to-transaction-btn" class="button">Convert to Estimated Transaction</button>
                            ` : ''}
                        </div>

                        <div id="finalize-form-container" class="hidden-form-container">
                            <h2 class="heading" style="font-size: 1.5em; margin-top: 20px;">Finalize Shopping Details</h2>
                            <form id="finalize-shopping-form" class="form" enctype="multipart/form-data">
                                <div class="input-group">
                                    <label for="transaction-date" class="label">Transaction Date:</label>
                                    <input type="date" id="transaction-date" class="input" value="${new Date().toISOString().slice(0, 10)}" required>
                                </div>
                                <div class="input-group">
                                    <label for="total-amount" class="label">Total Amount (Optional):</label>
                                    <input type="number" step="0.01" id="total-amount" class="input" placeholder="e.g., 55.75">
                                </div>
                                <div class="input-group">
                                    <label for="receipt-image" class="label">Receipt Image (Optional):</label>
                                    <input type="file" id="receipt-image" class="input">
                                </div>
                                <p class="small-info">Adjust 'Actual Qty' for each item above if needed, before submitting.</p>
                                <button type="submit" class="button">Confirm Finalize</button>
                                <button type="button" id="cancel-finalize-btn" class="button button-secondary">Cancel</button>
                                <p id="finalize-message" class="message"></p>
                            </form>
                        </div>

                        ${itemsHtml}

                        <button class="button" onclick="window.location.hash='#shopping-lists'" style="margin-top: 30px;">Back to Lists</button>
                    </div>
                `;

                // --- Add Event Listeners ---
                const finalizeListBtn = targetElement.querySelector('#finalize-list-btn');
                const finalizeFormContainer = targetElement.querySelector('#finalize-form-container');
                const finalizeShoppingForm = targetElement.querySelector('#finalize-shopping-form');
                const cancelFinalizeBtn = targetElement.querySelector('#cancel-finalize-btn');
                const finalizeMessage = targetElement.querySelector('#finalize-message');
                const deleteListBtn = targetElement.querySelector('#delete-list-btn');
                const convertToTransactionBtn = targetElement.querySelector('#convert-to-transaction-btn');


                // Show Finalize Form
                if (finalizeListBtn) {
                    finalizeListBtn.addEventListener('click', () => {
                        finalizeFormContainer.classList.remove('hidden-form-container');
                        finalizeMessage.textContent = '';
                        finalizeMessage.className = 'message';
                    });
                }

                // Cancel Finalize
                if (cancelFinalizeBtn) {
                    cancelFinalizeBtn.addEventListener('click', () => {
                        finalizeFormContainer.classList.add('hidden-form-container');
                        finalizeShoppingForm.reset();
                    });
                }

                // Finalize Shopping Form Submission
                if (finalizeShoppingForm) {
                    finalizeShoppingForm.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        renderLoadingSpinner(targetElement);
                        finalizeMessage.textContent = '';
                        finalizeMessage.className = 'message';

                        const transactionDate = finalizeShoppingForm.querySelector('#transaction-date').value;
                        const totalAmount = parseFloat(finalizeShoppingForm.querySelector('#total-amount').value) || null;
                        const receiptImageFile = finalizeShoppingForm.querySelector('#receipt-image').files[0];

                        const items = [];
                        targetElement.querySelectorAll('.shopping-list-item-card').forEach(card => {
                            const itemId = card.dataset.itemId;
                            const productId = card.dataset.productId;
                            const actualQtyInput = card.querySelector(`#actual-qty-${itemId}`);
                            const actual_quantity = actualQtyInput ? parseFloat(actualQtyInput.value) : null;

                            // Only include items that were updated or have a predicted quantity
                            // For simplicity, we send all items back with potentially updated actual_quantity
                            items.push({
                                item_id: parseInt(itemId),
                                product_id: parseInt(productId), // Make sure to send product_id
                                actual_quantity: actual_quantity
                            });
                        });

                        const formData = new FormData();
                        formData.append('transaction_date', transactionDate);
                        if (totalAmount !== null) {
                            formData.append('total_amount', totalAmount);
                        }
                        if (receiptImageFile) {
                            formData.append('receipt_image', receiptImageFile);
                        }
                        // Stringify the items array and append it
                        formData.append('items', JSON.stringify(items));


                        try {
                            const completeResponse = await completeShoppingList(list.id, formData);
                            removeLoadingSpinner(targetElement);

                            if (completeResponse.success) {
                                finalizeMessage.textContent = completeResponse.message || 'Shopping list finalized and transaction created!';
                                finalizeMessage.classList.add('success');
                                finalizeFormContainer.classList.add('hidden-form-container');
                                // Refresh the page to show updated status
                                fetchAndRenderList();
                            } else {
                                finalizeMessage.textContent = completeResponse.message || 'Failed to finalize shopping list.';
                                finalizeMessage.classList.add('error');
                                if (completeResponse.errors) {
                                    for (const key in completeResponse.errors) {
                                        finalizeMessage.innerHTML += `<br>${key}: ${completeResponse.errors[key].join(', ')}`;
                                    }
                                }
                            }
                        } catch (error) {
                            removeLoadingSpinner(targetElement);
                            console.error('Error finalizing shopping list:', error);
                            finalizeMessage.textContent = error.response?.data?.message || 'An unexpected error occurred.';
                            finalizeMessage.classList.add('error');
                        }
                    });
                }

                // Delete List Button
                if (deleteListBtn) {
                    deleteListBtn.addEventListener('click', async () => {
                        if (confirm(`Are you sure you want to delete Shopping List #${list.id}? This action cannot be undone.`)) {
                            renderLoadingSpinner(targetElement);
                            try {
                                await deleteShoppingList(list.id);
                                removeLoadingSpinner(targetElement);
                                alert('Shopping list deleted successfully!');
                                window.location.hash = '#shopping-lists'; // Go back to list page
                            } catch (error) {
                                removeLoadingSpinner(targetElement);
                                const errorMessage = error.response?.data?.message || 'Failed to delete shopping list.';
                                alert(`Error: ${errorMessage}`);
                            }
                        }
                    });
                }

                // Convert to Estimated Transaction Button
                if (convertToTransactionBtn) {
                    convertToTransactionBtn.addEventListener('click', async () => {
                        if (confirm(`Convert expired Shopping List #${list.id} to an estimated transaction?`)) {
                            renderLoadingSpinner(targetElement);
                            try {
                                const response = await convertExpiredToTransaction(list.id);
                                removeLoadingSpinner(targetElement);
                                if (response.success) {
                                    alert(response.message || 'Shopping list converted to estimated transaction successfully!');
                                    window.location.hash = `#transactions/${response.data.id}`; // Go to new transaction detail
                                } else {
                                    alert(`Error: ${response.message || 'Failed to convert list.'}`);
                                }
                            } catch (error) {
                                removeLoadingSpinner(targetElement);
                                const errorMessage = error.response?.data?.message || 'Failed to convert shopping list to transaction.';
                                alert(`Error: ${errorMessage}`);
                            }
                        }
                    });
                }


            } else {
                targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${response.message}</p></div>`;
            }
        } catch (error) {
            removeLoadingSpinner(targetElement);
            const errorMessage = error.response?.data?.message || `Failed to fetch shopping list #${id} details.`;
            targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${errorMessage}</p><button class="button" onclick="window.location.hash='#shopping-lists'" style="margin-top: 20px;">Back to Lists</button></div>`;
        }
    };

    // Initial fetch and render
    fetchAndRenderList();
}