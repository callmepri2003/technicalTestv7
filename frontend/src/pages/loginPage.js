// src/pages/loginPage.js
import { renderAuthForm } from '../components/authForm';
import { loginUser } from '../api/auth';
import { setAuthToken } from '../utils/authUtils';

export function renderLoginPage(targetElement, navigate, renderHeaderCallback) {
    const onSubmit = async (username, password) => {
        try {
            const data = await loginUser(username, password);
            setAuthToken(data.token);
            renderHeaderCallback(); // Re-render header to show logged-in state
            navigate('dashboard');
            return { success: true, message: data.message };
        } catch (error) {
            console.error('Login failed:', error.response?.data || error.message);
            return { success: false, message: error.response?.data?.message || 'Login failed.' };
        }
    };

    renderAuthForm(targetElement, onSubmit, true);
}