// src/utils/authUtils.js
export const setAuthToken = (token) => {
  localStorage.setItem('authToken', token);
};

export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

export const removeAuthToken = () => {
  localStorage.removeItem('authToken');
};

export const isAuthenticated = () => {
  return !!getAuthToken();
};

// Example function for logging in (assuming you have one)
export const login = (token) => {
    localStorage.setItem('authToken', token);
};

// This is the missing piece! Ensure your logout function is exported.
export const logout = () => {
    localStorage.removeItem('authToken');
    // You might also clear other session-related data here
};