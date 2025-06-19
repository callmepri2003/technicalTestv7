// src/pages/uploadTransactionsPage.js
import { createTransaction } from '../api/transactions';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderUploadTransactionsPage(targetElement, navigate) {
    targetElement.innerHTML = `
        <div class="container">
            <h1 class="heading">Upload Transactions (JSON)</h1>
            <p class="description-text">
                Paste your transaction data in JSON format below. Each object in the array should represent a transaction.
                <br>
                <strong>Required fields:</strong> <code>transaction_date</code> (YYYY-MM-DD), <code>products</code> (array of objects).
                <br>
                For each product: <code>product_id</code> (integer), <code>quantity</code> (number).
                <br>
                Optional fields: <code>total_amount</code> (number), <code>unit_price</code> (number for each product).
            </p>
            <form id="json-upload-form" class="form">
                <div class="input-group">
                    <label for="json-data" class="label">Transaction JSON Data:</label>
                    <textarea id="json-data" class="input textarea" rows="15" placeholder='[
    {
        "transaction_date": "2025-06-15",
        "total_amount": 75.20,
        "products": [
            {"product_id": 1, "quantity": 2, "unit_price": 5.50},
            {"product_id": 3, "quantity": 1, "unit_price": 12.00}
        ]
    },
    {
        "transaction_date": "2025-06-10",
        "products": [
            {"product_id": 2, "quantity": 0.5},
            {"product_id": 1, "quantity": 1}
        ]
    }
]'></textarea>
                </div>
                <button type="submit" class="button">Upload Transactions</button>
                <button type="button" id="cancel-upload-btn" class="button button-secondary">Cancel</button>
                <p id="upload-message" class="message"></p>
            </form>
        </div>
    `;

    const jsonUploadForm = targetElement.querySelector('#json-upload-form');
    const jsonDataTextarea = targetElement.querySelector('#json-data');
    const uploadMessage = targetElement.querySelector('#upload-message');
    const cancelUploadBtn = targetElement.querySelector('#cancel-upload-btn');

    cancelUploadBtn.addEventListener('click', () => {
        navigate('transactions'); // Go back to transactions list
    });

    jsonUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        renderLoadingSpinner(targetElement);
        uploadMessage.textContent = '';
        uploadMessage.className = 'message';

        const jsonString = jsonDataTextarea.value.trim();
        let transactionsData;

        try {
            transactionsData = JSON.parse(jsonString);
            if (!Array.isArray(transactionsData)) {
                throw new Error("JSON data must be an array of transaction objects.");
            }
            // Basic validation: check if each transaction has required fields
            for (const transaction of transactionsData) {
                if (!transaction.transaction_date || !transaction.products || !Array.isArray(transaction.products)) {
                    throw new Error("Each transaction must have a 'transaction_date' and a 'products' array.");
                }
                for (const product of transaction.products) {
                    if (typeof product.product_id !== 'number' || typeof product.quantity !== 'number') {
                        throw new Error("Each product must have 'product_id' (number) and 'quantity' (number).");
                    }
                }
            }

        } catch (error) {
            removeLoadingSpinner(targetElement);
            uploadMessage.textContent = `JSON validation error: ${error.message}`;
            uploadMessage.classList.add('error');
            console.error('JSON validation error:', error);
            return;
        }

        let successCount = 0;
        let failCount = 0;
        let errorDetails = [];

        for (const transaction of transactionsData) {
            try {
                // The API endpoint is designed to create a single transaction at a time.
                // We will loop through the provided JSON array and send each as a separate request.
                // If the backend was designed for bulk upload, we'd send the whole array.
                const response = await createTransaction(transaction);
                if (response.success) {
                    successCount++;
                } else {
                    failCount++;
                    errorDetails.push(`Transaction on ${transaction.transaction_date}: ${response.message || 'Unknown error.'}`);
                    if (response.errors) {
                         for (const key in response.errors) {
                            errorDetails.push(` - ${key}: ${response.errors[key].join(', ')}`);
                        }
                    }
                }
            } catch (error) {
                failCount++;
                const errorMessage = error.response?.data?.message || 'Network/Server error.';
                errorDetails.push(`Transaction on ${transaction.transaction_date}: ${errorMessage}`);
                if (error.response?.data?.errors) {
                    for (const key in error.response.data.errors) {
                        errorDetails.push(` - ${key}: ${error.response.data.errors[key].join(', ')}`);
                    }
                }
                console.error('Error uploading individual transaction:', transaction, error);
            }
        }

        removeLoadingSpinner(targetElement);
        let finalMessage = `Upload complete: ${successCount} successful, ${failCount} failed.`;
        if (failCount > 0) {
            finalMessage += `<br><br><strong>Errors:</strong><br>${errorDetails.join('<br>')}`;
            uploadMessage.classList.add('error');
        } else {
            uploadMessage.classList.add('success');
        }
        uploadMessage.innerHTML = finalMessage;

        // Optionally clear the textarea after successful upload
        if (successCount > 0 && failCount === 0) {
            jsonDataTextarea.value = '';
        }
    });
}