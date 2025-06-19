// src/pages/transactionDetailPage.js
import { getTransactionDetail } from '../api/transactions';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderTransactionDetailPage(targetElement, id) {
    renderLoadingSpinner(targetElement);

    try {
        const response = await getTransactionDetail(id);
        removeLoadingSpinner(targetElement);

        if (response.success) {
            const tx = response.data;
            const typeClass = `type-${tx.transaction_type.toLowerCase()}`;
            const totalAmount = tx.total_amount ? parseFloat(tx.total_amount).toFixed(2) : 'N/A';

            let productsHtml = '';
            if (tx.products && tx.products.length > 0) {
                productsHtml = `
                    <h3>Products Purchased:</h3>
                    <div class="card-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                        ${tx.products.map(product => `
                            <div class="card small-card">
                                <p><strong>Product:</strong> ${product.product.name}</p>
                                <p><strong>Category:</strong> ${product.product.category || 'N/A'}</p>
                                <p><strong>Quantity:</strong> ${product.quantity} ${product.product.default_unit || 'item'}</p>
                                <p><strong>Unit Price:</strong> $${product.unit_price !== null ? parseFloat(product.unit_price).toFixed(2) : 'N/A'}</p>
                                <p><strong>Total Price:</strong> $${product.total_price !== null ? parseFloat(product.total_price).toFixed(2) : 'N/A'}</p>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                productsHtml = '<p class="no-data-message" style="margin-top: 15px;">No products recorded for this transaction.</p>';
            }

            targetElement.innerHTML = `
                <div class="container">
                    <h1 class="heading">Transaction Details: #${tx.id}</h1>
                    <div class="detail-section">
                        <p><strong>Transaction Date:</strong> ${tx.transaction_date}</p>
                        <p><strong>Type:</strong> <span class="${typeClass}">${tx.transaction_type}</span></p>
                        <p><strong>Total Amount:</strong> $${totalAmount}</p>
                        ${tx.receipt_image ? `<p><strong>Receipt:</strong> <a href="${tx.receipt_image}" target="_blank">View Receipt</a></p>` : ''}
                        <p><strong>Created At:</strong> ${new Date(tx.created_at).toLocaleString()}</p>
                    </div>
                    ${productsHtml}
                    <button class="button" onclick="window.location.hash='#transactions'" style="margin-top: 30px;">Back to Transactions</button>
                </div>
            `;
        } else {
            targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${response.message}</p></div>`;
        }
    } catch (error) {
        removeLoadingSpinner(targetElement);
        const errorMessage = error.response?.data?.message || `Failed to fetch transaction #${id} details.`;
        targetElement.innerHTML = `<div class="container"><p class="message error">Error: ${errorMessage}</p><button class="button" onclick="window.location.hash='#transactions'" style="margin-top: 20px;">Back to Transactions</button></div>`;
    }
}