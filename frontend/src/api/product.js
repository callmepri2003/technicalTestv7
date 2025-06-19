// src/api/product.js
import api from './axiosConfig';

/**
 * Fetches a list of products.
 * @param {Object} [params={}] - Query parameters for filtering, pagination (e.g., {page: 1, search: 'milk'}).
 * @returns {Promise<Object>} A paginated list of products.
 */
export const getProducts = async (params = {}) => {
    const response = await api.get('/products/', { params });
    return response.data;
};

/**
 * Creates a new product.
 * @param {Object} data - The product data (e.g., {name: "Milk", category: "Dairy", default_unit: "L"}).
 * @returns {Promise<Object>} The newly created product.
 */
export const createProduct = async (data) => {
    const response = await api.post('/products/', data);
    return response.data;
};

/**
 * Fetches details of a specific product.
 * @param {number} id - The ID of the product.
 * @returns {Promise<Object>} The product details.
 */
export const getProductDetail = async (id) => {
    const response = await api.get(`/products/${id}/`);
    return response.data;
};

/**
 * Updates an existing product.
 * @param {number} id - The ID of the product to update.
 * @param {Object} data - The updated product data.
 * @returns {Promise<Object>} The updated product.
 */
export const updateProduct = async (id, data) => {
    const response = await api.put(`/products/${id}/`, data);
    return response.data;
};

/**
 * Deletes a product.
 * @param {number} id - The ID of the product to delete.
 * @returns {Promise<Object>} A success message.
 */
export const deleteProduct = async (id) => {
    const response = await api.delete(`/products/${id}/`);
    return response.data;
};