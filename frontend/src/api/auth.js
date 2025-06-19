// src/api/auth.js
import api from './axiosConfig';

export const loginUser = async (username, password) => {
  const response = await api.post('/auth/login/', { username, password });
  return response.data;
};

export const logoutUser = async () => {
  const response = await api.post('/auth/logout/');
  return response.data;
};