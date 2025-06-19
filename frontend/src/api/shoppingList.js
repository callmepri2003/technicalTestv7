// src/api/shoppingList.js
import api from './axiosConfig';

export const getShoppingLists = async (params = {}) => {
  const response = await api.get('/shopping-list', { params });
  return response.data;
};
// Add more shopping list API calls here as needed