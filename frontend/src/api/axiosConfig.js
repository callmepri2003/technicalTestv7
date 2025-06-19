// src/api/axiosConfig.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Optional: Handle 401 Unauthorized globally, e.g., redirect to login
    if (error.response && error.response.status === 401) {
      console.warn('Unauthorized request. Redirecting to login.');
      localStorage.removeItem('authToken');
      window.location.hash = '#login';
    }
    return Promise.reject(error);
  }
);

export default api;