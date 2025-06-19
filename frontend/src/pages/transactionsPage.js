// src/pages/transactionsPage.js
import { getTransactions } from '../api/transactions';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderTransactionsPage(targetElement) {
    renderLoadingSpinner(targetElement);

    try {
        const response = await getTransactions();
        removeLoadingSpinner(targetElement);

        if (response.success) {
            const transactions = response.data.results;
            let transactionHtml = '';
            if (transactions.length === 0) {
                transactionHtml = '<p class="no-data-message">No transactions found. Start recording your purchases!</p>';
            } else {
                transactionHtml = transactions.map(tx => {
                    const typeClass = `type-${tx.transaction_type.toLowerCase()}`;
                    const totalAmount = tx.total_amount ? parseFloat(tx.total_amount).toFixed(2) : 'N/A';
                    return `
                        <div class="card">
                            <h3 class="card-title">Transaction #${tx.id}</h3>
                            <p><strong>Date:</strong> ${tx.transaction_date}</p>
                            <p><strong>Type:</strong> <span class="${typeClass}">${tx.transaction_type}</span></p>
                            <p><strong>Total:</strong> $${totalAmount}</p>
                            <p><strong>Products:</strong> ${tx.products ? tx.products.length : 0}</p>
                            <button class="card-button">View Details</button>
                        </div>
                    `;
                }).join('');
                transactionHtml = `<div class="card-grid">${transactionHtml}</div>`;
            }

            targetElement.innerHTML = `
                <div class="container">
                    <h1 class="heading">Your Transactions</h1>
                    ${transactionHtml}
                </div>
            `;
        } else {
            targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${response.message}</p></div>`;
        }
    } catch (error) {
        removeLoadingSpinner(targetElement);
        const errorMessage = error.response?.data?.message || 'Failed to fetch transactions.';
        targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${errorMessage}</p></div>`;
    }
}