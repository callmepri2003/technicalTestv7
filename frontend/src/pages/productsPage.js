// src/pages/productsPage.js
import { getProducts, createProduct, updateProduct, deleteProduct } from '../api/product';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderProductsPage(targetElement, navigate) {
    let currentPage = 1;
    let totalPages = 1;
    let currentSearchTerm = '';
    let currentCategory = ''; // For filtering by category

    // This is a simple list of common units for the dropdown
    const commonUnits = ["pcs", "kg", "g", "L", "ml", "pack", "bottle", "can", "box", "bag", "roll", "sheet", "set", "pair"];
    // This could be fetched from the API if you had a categories endpoint
    const commonCategories = ["Dairy & Cheese", "Fruits", "Vegetables", "Meat & Poultry", "Seafood",
                              "Bakery", "Pantry Staples", "Beverages", "Snacks", "Frozen Foods",
                              "Household", "Personal Care", "Pet Supplies", "Other"];


    async function fetchAndRenderProducts() {
        renderLoadingSpinner(targetElement);
        try {
            const params = {
                page: currentPage,
                search: currentSearchTerm || undefined,
                category: currentCategory || undefined,
                page_size: 10 // Adjust as needed
            };
            const response = await getProducts(params);
            removeLoadingSpinner(targetElement);

            if (response.success) {
                const products = response.data.results;
                totalPages = Math.ceil(response.data.count / params.page_size);

                let productsHtml = '';
                if (products.length === 0) {
                    productsHtml = '<p class="no-data-message">No products found. Add a new one!</p>';
                } else {
                    productsHtml = `
                        <div class="card-grid">
                            ${products.map(product => `
                                <div class="card product-card" data-id="${product.id}">
                                    <h3 class="card-title">${product.name}</h3>
                                    <p><strong>Category:</strong> ${product.category || 'N/A'}</p>
                                    <p><strong>Default Unit:</strong> ${product.default_unit || 'N/A'}</p>
                                    <div class="card-actions">
                                        <button class="button button-small edit-product-btn" data-id="${product.id}">Edit</button>
                                        <button class="button button-small button-danger delete-product-btn" data-id="${product.id}">Delete</button>
                                    </div>
                                    <div class="edit-form-container hidden">
                                        <h4>Edit Product</h4>
                                        <form class="edit-product-form" data-id="${product.id}">
                                            <div class="input-group">
                                                <label for="edit-name-${product.id}" class="label">Name:</label>
                                                <input type="text" id="edit-name-${product.id}" class="input" value="${product.name}" required>
                                            </div>
                                            <div class="input-group">
                                                <label for="edit-category-${product.id}" class="label">Category:</label>
                                                <select id="edit-category-${product.id}" class="input">
                                                    <option value="">Select Category</option>
                                                    ${commonCategories.map(cat => `<option value="${cat}" ${product.category === cat ? 'selected' : ''}>${cat}</option>`).join('')}
                                                </select>
                                            </div>
                                            <div class="input-group">
                                                <label for="edit-unit-${product.id}" class="label">Default Unit:</label>
                                                <select id="edit-unit-${product.id}" class="input">
                                                    <option value="">Select Unit</option>
                                                    ${commonUnits.map(unit => `<option value="${unit}" ${product.default_unit === unit ? 'selected' : ''}>${unit}</option>`).join('')}
                                                </select>
                                            </div>
                                            <button type="submit" class="button button-small">Update</button>
                                            <button type="button" class="button button-small button-secondary cancel-edit-btn" data-id="${product.id}">Cancel</button>
                                            <p class="edit-message message" id="edit-message-${product.id}"></p>
                                        </form>
                                    </div>
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

                targetElement.querySelector('#products-list-container').innerHTML = productsHtml;

                // Add event listeners for pagination
                targetElement.querySelector('#prev-page').addEventListener('click', () => {
                    if (currentPage > 1) {
                        currentPage--;
                        fetchAndRenderProducts();
                    }
                });
                targetElement.querySelector('#next-page').addEventListener('click', () => {
                    if (currentPage < totalPages) {
                        currentPage++;
                        fetchAndRenderProducts();
                    }
                });

                // Add event listeners for edit and delete buttons
                targetElement.querySelectorAll('.edit-product-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const productId = e.target.dataset.id;
                        const card = e.target.closest('.product-card');
                        card.querySelector('.edit-form-container').classList.remove('hidden');
                        card.querySelector('.card-actions').classList.add('hidden'); // Hide original buttons
                        card.querySelector(`#edit-message-${productId}`).textContent = ''; // Clear message
                    });
                });

                targetElement.querySelectorAll('.cancel-edit-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const productId = e.target.dataset.id;
                        const card = e.target.closest('.product-card');
                        card.querySelector('.edit-form-container').classList.add('hidden');
                        card.querySelector('.card-actions').classList.remove('hidden'); // Show original buttons
                    });
                });


                targetElement.querySelectorAll('.edit-product-form').forEach(form => {
                    form.addEventListener('submit', async (e) => {
                        e.preventDefault();
                        const productId = e.target.dataset.id;
                        const name = form.querySelector(`#edit-name-${productId}`).value;
                        const category = form.querySelector(`#edit-category-${productId}`).value;
                        const default_unit = form.querySelector(`#edit-unit-${productId}`).value;
                        const messageElement = form.querySelector(`#edit-message-${productId}`);

                        messageElement.textContent = '';
                        messageElement.className = 'message';

                        // Basic validation
                        if (!name) {
                            messageElement.textContent = 'Product name is required.';
                            messageElement.classList.add('error');
                            return;
                        }

                        renderLoadingSpinner(form); // Show spinner next to form
                        try {
                            const response = await updateProduct(productId, { name, category, default_unit });
                            removeLoadingSpinner(form); // Remove spinner

                            if (response.success) {
                                messageElement.textContent = response.message || 'Product updated successfully!';
                                messageElement.classList.add('success');
                                setTimeout(() => fetchAndRenderProducts(), 1000); // Re-fetch after a short delay
                            } else {
                                messageElement.textContent = response.message || 'Failed to update product.';
                                messageElement.classList.add('error');
                                if (response.errors) {
                                    for (const key in response.errors) {
                                        messageElement.innerHTML += `<br>${key}: ${response.errors[key].join(', ')}`;
                                    }
                                }
                            }
                        } catch (error) {
                            removeLoadingSpinner(form); // Remove spinner
                            console.error('Error updating product:', error);
                            messageElement.textContent = error.response?.data?.message || 'An unexpected error occurred.';
                            messageElement.classList.add('error');
                        }
                    });
                });


                targetElement.querySelectorAll('.delete-product-btn').forEach(button => {
                    button.addEventListener('click', async (e) => {
                        const productId = e.target.dataset.id;
                        if (confirm(`Are you sure you want to delete product ID: ${productId}? This action cannot be undone.`)) {
                            renderLoadingSpinner(targetElement);
                            try {
                                const response = await deleteProduct(productId);
                                removeLoadingSpinner(targetElement);
                                if (response.success) {
                                    alert(response.message || 'Product deleted successfully!');
                                    fetchAndRenderProducts(); // Re-fetch list
                                } else {
                                    alert(`Error: ${response.message || 'Failed to delete product.'}`);
                                }
                            } catch (error) {
                                removeLoadingSpinner(targetElement);
                                console.error('Error deleting product:', error);
                                alert(`An error occurred: ${error.response?.data?.message || 'Could not delete product.'}`);
                            }
                        }
                    });
                });

            } else {
                targetElement.querySelector('#products-list-container').innerHTML = `<p class="message error">Error: ${response.message}</p>`;
            }
        } catch (error) {
            removeLoadingSpinner(targetElement);
            console.error('Error fetching products:', error);
            targetElement.querySelector('#products-list-container').innerHTML = `<p class="message error">Failed to load products.</p>`;
        }
    }

    targetElement.innerHTML = `
        <div class="container">
            <h1 class="heading">Products</h1>

            <div class="add-new-section">
                <button id="toggle-add-product-form" class="button">Add New Product</button>
                <div id="add-product-form-container" class="hidden-form-container">
                    <h2 class="sub-heading">Add New Product</h2>
                    <form id="add-product-form" class="form">
                        <div class="input-group">
                            <label for="product-name" class="label">Product Name:</label>
                            <input type="text" id="product-name" class="input" required>
                        </div>
                        <div class="input-group">
                            <label for="product-category" class="label">Category:</label>
                            <select id="product-category" class="input">
                                <option value="">Select Category</option>
                                ${commonCategories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                            </select>
                        </div>
                        <div class="input-group">
                            <label for="product-unit" class="label">Default Unit:</label>
                            <select id="product-unit" class="input" required>
                                <option value="">Select Unit</option>
                                ${commonUnits.map(unit => `<option value="${unit}">${unit}</option>`).join('')}
                            </select>
                        </div>
                        <button type="submit" class="button">Create Product</button>
                        <button type="button" id="cancel-add-product" class="button button-secondary">Cancel</button>
                        <p id="add-product-message" class="message"></p>
                    </form>
                </div>
            </div>

            <div class="filters">
                <input type="text" id="search-product" class="input" placeholder="Search by name...">
                <select id="filter-category" class="input">
                    <option value="">All Categories</option>
                    ${commonCategories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                </select>
                <button id="apply-product-filters" class="button">Apply Filters</button>
                <button id="clear-product-filters" class="button button-secondary">Clear Filters</button>
            </div>

            <div id="products-list-container">
                </div>
        </div>
    `;

    // Get elements for Add Product Form
    const toggleAddProductFormBtn = targetElement.querySelector('#toggle-add-product-form');
    const addProductFormContainer = targetElement.querySelector('#add-product-form-container');
    const addProductForm = targetElement.querySelector('#add-product-form');
    const productNameInput = targetElement.querySelector('#product-name');
    const productCategoryInput = targetElement.querySelector('#product-category');
    const productUnitInput = targetElement.querySelector('#product-unit');
    const addProductMessage = targetElement.querySelector('#add-product-message');
    const cancelAddProductBtn = targetElement.querySelector('#cancel-add-product');

    // Toggle Add Product Form Visibility
    toggleAddProductFormBtn.addEventListener('click', () => {
        addProductFormContainer.classList.toggle('hidden-form-container');
        addProductMessage.textContent = ''; // Clear any previous messages
        addProductMessage.className = 'message';
        addProductForm.reset();
    });

    cancelAddProductBtn.addEventListener('click', () => {
        addProductFormContainer.classList.add('hidden-form-container');
        addProductForm.reset();
        addProductMessage.textContent = '';
        addProductMessage.className = 'message';
    });

    // Handle Add Product Form Submission
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        addProductMessage.textContent = ''; // Clear previous messages
        addProductMessage.className = 'message'; // Reset class

        const name = productNameInput.value.trim();
        const category = productCategoryInput.value.trim();
        const default_unit = productUnitInput.value.trim();

        // Basic validation
        if (!name || !default_unit) {
            addProductMessage.textContent = 'Product name and default unit are required.';
            addProductMessage.classList.add('error');
            return;
        }

        renderLoadingSpinner(addProductForm); // Show spinner next to form
        try {
            const response = await createProduct({ name, category, default_unit });
            removeLoadingSpinner(addProductForm); // Remove spinner

            if (response.success) {
                addProductMessage.textContent = response.message || 'Product created successfully!';
                addProductMessage.classList.add('success');
                addProductForm.reset(); // Clear the form
                fetchAndRenderProducts(); // Refresh the list
            } else {
                addProductMessage.textContent = response.message || 'Failed to create product.';
                addProductMessage.classList.add('error');
                if (response.errors) {
                    for (const key in response.errors) {
                        addProductMessage.innerHTML += `<br>${key}: ${response.errors[key].join(', ')}`;
                    }
                }
            }
        } catch (error) {
            removeLoadingSpinner(addProductForm); // Remove spinner
            console.error('Error creating product:', error);
            addProductMessage.textContent = error.response?.data?.message || 'An unexpected error occurred.';
            addProductMessage.classList.add('error');
        }
    });

    // Get elements for filters
    const searchProductInput = targetElement.querySelector('#search-product');
    const filterCategorySelect = targetElement.querySelector('#filter-category');
    const applyFiltersBtn = targetElement.querySelector('#apply-product-filters');
    const clearFiltersBtn = targetElement.querySelector('#clear-product-filters');

    // Event Listeners for Filters
    applyFiltersBtn.addEventListener('click', () => {
        currentSearchTerm = searchProductInput.value.trim();
        currentCategory = filterCategorySelect.value;
        currentPage = 1; // Reset to first page on new filters
        fetchAndRenderProducts();
    });

    clearFiltersBtn.addEventListener('click', () => {
        searchProductInput.value = '';
        filterCategorySelect.value = '';
        currentSearchTerm = '';
        currentCategory = '';
        currentPage = 1;
        fetchAndRenderProducts();
    });

    // Initial load of products
    fetchAndRenderProducts();
}