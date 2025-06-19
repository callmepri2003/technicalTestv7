// src/api/transactions.js
import api from './axiosConfig';

export const getTransactions = async (params = {}) => {
  const response = await api.get('/transactions', { params });
  return response.data;
};
// Add more transaction API calls here as needed