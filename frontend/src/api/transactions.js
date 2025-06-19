// src/api/transactions.js
import api from './axiosConfig';

export const getTransactions = async (params = {}) => {
  const response = await api.get('/transactions/', { params });
  return response.data;
};

// THIS IS THE LINE THAT NEEDS 'export'
export const createTransaction = async (transactionData) => {
  const response = await api.post('/transactions/', transactionData);
  return response.data;
};

export const getTransactionDetail = async (id) => {
  const response = await api.get(`/transactions/${id}/`);
  return response.data;
};

export const updateTransaction = async (id, transactionData) => {
  const response = await api.put(`/transactions/${id}/`, transactionData);
  return response.data;
};

export const deleteTransaction = async (id) => {
  const response = await api.delete(`/transactions/${id}/`);
  return response.data;
};

export const estimateMissedTransaction = async (data) => {
  const response = await api.post('/transactions/estimate-missed/', data);
  return response.data;
};