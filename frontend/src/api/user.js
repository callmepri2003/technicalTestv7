// src/api/user.js
import api from './axiosConfig';

/**
 * Fetches the current user's profile data.
 * @returns {Promise<Object>} The user data, or an error response.
 */
export const getMyProfile = async () => {
    const response = await api.get('/users/me/');
    return response.data;
};

/**
 * Updates the current user's profile data.
 * @param {Object} data - The updated user data (e.g., {first_name: "New", last_name: "User"}).
 * @returns {Promise<Object>} The updated user data, or an error response.
 */
export const updateMyProfile = async (data) => {
    const response = await api.put('/users/me/', data);
    return response.data;
};