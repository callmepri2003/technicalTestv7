// src/pages/transactionsPage.js
import { getTransactions } from '../api/transactions';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderTransactionsPage(targetElement, navigate) {
    let currentPage = 1;
    let totalPages = 1;
    let currentTransactionType = '';
    let currentDateFrom = '';
    let currentDateTo = '';

    // Step 1: Immediately render the basic structure of the page.
    targetElement.innerHTML = `
        <div class="container">
            <h1 class="heading">Transactions</h1>

            <div class="section-controls">
                <button id="upload-json-btn" class="button">Upload Transactions (JSON)</button>
            </div>

            <div class="filters">
                <select id="filter-type" class="input">
                    <option value="">All Types</option>
                    <option value="ACTUAL">Actual</option>
                    <option value="ESTIMATED">Estimated</option>
                </select>
                <input type="date" id="filter-date-from" class="input" placeholder="Date From (YYYY-MM-DD)">
                <input type="date" id="filter-date-to" class="input" placeholder="Date To (YYYY-MM-DD)">
                <button id="apply-filters" class="button">Apply Filters</button>
                <button id="clear-filters" class="button button-secondary">Clear Filters</button>
            </div>

            <div id="transactions-list-container">
                <p class="message info">Loading transactions...</p> </div>
        </div>
    `;

    // Step 2: Get elements for filters and controls *after* they are in the DOM
    const filterType = targetElement.querySelector('#filter-type');
    const filterDateFrom = targetElement.querySelector('#filter-date-from');
    const filterDateTo = targetElement.querySelector('#filter-date-to');
    const applyFiltersBtn = targetElement.querySelector('#apply-filters');
    const clearFiltersBtn = targetElement.querySelector('#clear-filters');
    const uploadJsonBtn = targetElement.querySelector('#upload-json-btn');

    // Step 3: Define the fetch and render function
    async function fetchAndRenderTransactions() {
        // Only show global spinner if it's the initial load or a full refresh needed
        // Otherwise, the inner HTML update will serve as feedback
        // renderLoadingSpinner(targetElement); // Consider if you want a global spinner always

        // Ensure we always target the correct container for updates
        const listContainer = targetElement.querySelector('#transactions-list-container');
        if (!listContainer) {
            console.error("Error: #transactions-list-container not found in DOM.");
            return; // Exit if the container isn't there
        }
        listContainer.innerHTML = '<p class="message info">Loading transactions...</p>'; // Show loading inside container

        try {
            const params = {
                page: currentPage,
                transaction_type: currentTransactionType || undefined,
                date_from: currentDateFrom || undefined,
                date_to: currentDateTo || undefined,
                page_size: 10
            };
            const response = await getTransactions(params);
            // removeLoadingSpinner(targetElement); // Remove global spinner if used

            if (response.success) {
                const transactions = response.data.results;
                totalPages = Math.ceil(response.data.count / params.page_size);

                let transactionsHtml = '';
                if (transactions.length === 0) {
                    transactionsHtml = '<p class="no-data-message">No transactions found matching your criteria. Try adding one!</p>';
                } else {
                    transactionsHtml = `
                        <div class="card-grid">
                            ${transactions.map(transaction => `
                                <div class="card">
                                    <h3 class="card-title">Transaction ID: ${transaction.id}</h3>
                                    <p><strong>Date:</strong> <span class="math-inline">\{transaction\.transaction\_date\}</p\>
<p\><strong\>Type\:</strong\> <span class\="status\-</span>{transaction.transaction_type.toLowerCase()}">${transaction.transaction_type}</span></p>
                                    <p><strong>Total Amount:</strong> $${transaction.total_amount ? transaction.total_amount.toFixed(2) : 'N/A'}</p>
                                    <p><strong>Products:</strong> <span class="math-inline">\{transaction\.products\.length\}</p\>
<button class\="card\-button view\-details\-btn" data\-id\="</span>{transaction.id}">View Details</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="pagination-controls">
                            <button id="prev-page" class="button" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                            <span>Page ${currentPage} of ${totalPages}</span>
                            <button id="next-page" class="button" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        </div>
                    `;
                }

                listContainer.innerHTML = transactionsHtml; // <--- This line should now work correctly

                // Add event listeners for pagination *after* they are in the DOM
                const prevPageBtn = listContainer.querySelector('#prev-page');
                const nextPageBtn = listContainer.querySelector('#next-page');

                if (prevPageBtn) {
                    prevPageBtn.addEventListener('click', () => {
                        if (currentPage > 1) {
                            currentPage--;
                            fetchAndRenderTransactions();
                        }
                    });
                }
                if (nextPageBtn) {
                    nextPageBtn.addEventListener('click', () => {
                        if (currentPage < totalPages) {
                            currentPage++;
                            fetchAndRenderTransactions();
                        }
                    });
                }

                // Add event listeners for "View Details"
                listContainer.querySelectorAll('.view-details-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const id = e.target.dataset.id;
                        if (id) {
                            navigate(`transactions/${id}`);
                        }
                    });
                });

            } else {
                listContainer.innerHTML = `<p class="message error">Error: ${response.message}</p>`;
            }
        } catch (error) {
            // removeLoadingSpinner(targetElement); // Remove global spinner if used
            console.error('Error fetching transactions:', error);
            listContainer.innerHTML = `<p class="message error">Failed to load transactions.</p>`;
        }
    }

    // Step 4: Add Event Listeners for Filters
    applyFiltersBtn.addEventListener('click', () => {
        currentTransactionType = filterType.value;
        currentDateFrom = filterDateFrom.value;
        currentDateTo = filterDateTo.value;
        currentPage = 1; // Reset to first page on new filters
        fetchAndRenderTransactions();
    });

    clearFiltersBtn.addEventListener('click', () => {
        filterType.value = '';
        filterDateFrom.value = '';
        filterDateTo.value = '';
        currentTransactionType = '';
        currentDateFrom = '';
        currentDateTo = '';
        currentPage = 1;
        fetchAndRenderTransactions();
    });

    // Event Listener for JSON Upload Button
    if (uploadJsonBtn) {
        uploadJsonBtn.addEventListener('click', () => {
            navigate('upload-transactions');
        });
    }

    // Step 5: Initial load of transactions - now called *after* the initial HTML setup
    fetchAndRenderTransactions();
}