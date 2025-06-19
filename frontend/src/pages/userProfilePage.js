// src/pages/userProfilePage.js
import { getMyProfile, updateMyProfile } from '../api/user';
import { renderLoadingSpinner, removeLoadingSpinner } from '../components/loadingSpinner';

export async function renderUserProfilePage(targetElement) {
    targetElement.innerHTML = `
        <div class="container">
            <h1 class="heading">User Profile</h1>
            <p id="profile-loading-message" class="message info">Loading profile...</p>
            <form id="profile-form" class="form hidden">
                <div class="input-group">
                    <label for="username" class="label">Username:</label>
                    <input type="text" id="username" class="input" readonly>
                </div>
                <div class="input-group">
                    <label for="email" class="label">Email:</label>
                    <input type="email" id="email" class="input">
                </div>
                <div class="input-group">
                    <label for="first-name" class="label">First Name:</label>
                    <input type="text" id="first-name" class="input">
                </div>
                <div class="input-group">
                    <label for="last-name" class="label">Last Name:</label>
                    <input type="text" id="last-name" class="input">
                </div>
                <button type="submit" class="button">Save Changes</button>
                <p id="profile-message" class="message"></p>
            </form>
            <button class="button" onclick="window.location.hash='#dashboard'" style="margin-top: 30px;">Back to Dashboard</button>
        </div>
    `;

    const profileLoadingMessage = targetElement.querySelector('#profile-loading-message');
    const profileForm = targetElement.querySelector('#profile-form');
    const usernameInput = targetElement.querySelector('#username');
    const emailInput = targetElement.querySelector('#email');
    const firstNameInput = targetElement.querySelector('#first-name');
    const lastNameInput = targetElement.querySelector('#last-name');
    const profileMessage = targetElement.querySelector('#profile-message');

    const fetchUserProfile = async () => {
        profileLoadingMessage.classList.remove('hidden');
        profileForm.classList.add('hidden');
        renderLoadingSpinner(targetElement); // Show a global loading spinner too
        try {
            const response = await getMyProfile();
            removeLoadingSpinner(targetElement); // Remove global loading spinner
            if (response.success) {
                const user = response.data;
                usernameInput.value = user.username || '';
                emailInput.value = user.email || '';
                firstNameInput.value = user.first_name || '';
                lastNameInput.value = user.last_name || '';

                profileLoadingMessage.classList.add('hidden');
                profileForm.classList.remove('hidden');
            } else {
                profileLoadingMessage.textContent = response.message || 'Failed to load user profile.';
                profileLoadingMessage.classList.add('error');
            }
        } catch (error) {
            removeLoadingSpinner(targetElement); // Remove global loading spinner
            console.error('Error fetching user profile:', error);
            profileLoadingMessage.textContent = error.response?.data?.message || 'An unexpected error occurred while loading profile.';
            profileLoadingMessage.classList.add('error');
        }
    };

    const handleProfileSubmit = async (e) => {
        e.preventDefault();
        profileMessage.textContent = '';
        profileMessage.className = 'message'; // Reset message styling

        const updatedData = {
            email: emailInput.value,
            first_name: firstNameInput.value,
            last_name: lastNameInput.value,
        };

        renderLoadingSpinner(profileForm); // Show loading spinner within the form
        try {
            const response = await updateMyProfile(updatedData);
            removeLoadingSpinner(profileForm); // Remove loading spinner

            if (response.success) {
                profileMessage.textContent = response.message || 'Profile updated successfully!';
                profileMessage.classList.add('success');
            } else {
                profileMessage.textContent = response.message || 'Failed to update profile.';
                profileMessage.classList.add('error');
                if (response.errors) {
                    for (const key in response.errors) {
                        profileMessage.innerHTML += `<br>${key}: ${response.errors[key].join(', ')}`;
                    }
                }
            }
        } catch (error) {
            removeLoadingSpinner(profileForm); // Remove loading spinner
            console.error('Error updating user profile:', error);
            profileMessage.textContent = error.response?.data?.message || 'An unexpected error occurred during update.';
            profileMessage.classList.add('error');
        }
    };

    profileForm.addEventListener('submit', handleProfileSubmit);

    // Initial fetch when the page loads
    fetchUserProfile();
}