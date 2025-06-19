// src/components/loadingSpinner.js
export function renderLoadingSpinner(targetElement) {
    targetElement.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
            <p class="loading-text">Loading...</p>
        </div>
    `;
}

export function removeLoadingSpinner(targetElement) {
    const spinner = targetElement.querySelector('.spinner-container');
    if (spinner) {
        spinner.remove();
    }
}