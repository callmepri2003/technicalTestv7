// src/components/authForm.js
export function renderAuthForm(targetElement, onSubmit, isLogin = true) {
    const formTitle = isLogin ? 'Login' : 'Sign Up';

    targetElement.innerHTML = `
        <div class="container">
            <h2 class="heading">${formTitle}</h2>
            <form id="auth-form" class="form">
                <div class="input-group">
                    <label for="username" class="label">Username:</label>
                    <input type="text" id="username" class="input" required>
                </div>
                <div class="input-group">
                    <label for="password" class="label">Password:</label>
                    <input type="password" id="password" class="input" required>
                </div>
                <button type="submit" class="button">${formTitle}</button>
                <p id="auth-message" class="message"></p>
            </form>
        </div>
    `;

    const authForm = targetElement.querySelector('#auth-form');
    const authMessage = targetElement.querySelector('#auth-message');

    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = authForm.querySelector('#username').value;
        const password = authForm.querySelector('#password').value;

        authMessage.textContent = '';
        authMessage.className = 'message'; // Reset classes

        const result = await onSubmit(username, password);
        authMessage.textContent = result.message;
        authMessage.classList.add(result.success ? 'success' : 'error');
    });
}