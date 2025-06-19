// src/api/shoppingList.js
import api from './axiosConfig';

export const getShoppingLists = async (params = {}) => {
  const response = await api.get('/shopping-lists/', { params });
  return response.data;
};

export const generateShoppingLists = async (data) => {
  const response = await api.post('/shopping-lists/generate/', data);
  return response.data;
};

export const getShoppingListDetail = async (id) => {
  const response = await api.get(`/shopping-lists/${id}/`);
  return response.data;
};

// NEW: Update a shopping list
export const updateShoppingList = async (id, data) => {
  const response = await api.put(`/shopping-lists/${id}/`, data);
  return response.data;
};

// NEW: Delete a shopping list
export const deleteShoppingList = async (id) => {
  const response = await api.delete(`/shopping-lists/${id}/`);
  return response.data;
};

// NEW: Complete a shopping list and create a transaction
export const completeShoppingList = async (id, formData) => { // Expects FormData
  const response = await api.post(`/shopping-lists/${id}/complete/`, formData);
  return response.data;
};

// NEW: Convert expired list to estimated transaction
export const convertExpiredToTransaction = async (id) => {
  const response = await api.post(`/shopping-lists/${id}/convert-to-transaction/`);
  return response.data;
};