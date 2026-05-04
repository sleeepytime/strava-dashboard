// ui.js

/**
 * Syncs the visual state of filters.
 * @param {NodeList} presetButtons - The collection of preset filter buttons
 * @param {HTMLElement} startInput - The start date input element
 * @param {HTMLElement} endInput - The end date input element
 * @param {HTMLElement|null} activeElement - The specific element to highlight (or null)
 */
export function updateFilterFocus(presetButtons, startInput, endInput, activeElement = null) {
    // 1. Remove 'active' from all preset buttons
    presetButtons.forEach(btn => btn.classList.remove("active"));
    
    // 2. Remove 'active' from both date inputs
    startInput.classList.remove("active");
    endInput.classList.remove("active");

    // 3. Add 'active' to the triggered element
    if (activeElement) {
        activeElement.classList.add("active");
    }
}

export function animateTransition(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.classList.remove("fade-in");
        void el.offsetWidth;
        el.classList.add("fade-in");
    }
}

/**
 * Toggles between a data container and its empty-state placeholder.
 * @param {string} containerId - ID of the div holding your charts/data
 * @param {string} placeholderId - ID of the empty-state div
 * @param {boolean} hasData - Result of your data check
 */
export function switchContentState(containerId, placeholderId, hasData) {
    const container = document.getElementById(containerId);
    const placeholder = document.getElementById(placeholderId);

    if (hasData) {
        container.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        container.style.display = 'none';
        placeholder.style.display = 'flex';
    }
}