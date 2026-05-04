// app.js
import {
    loadStats, updateStatsDateRange
} from './stats.js';
import {
    renderTimeline, loadTimeline, setActiveDay, resetDaySelection
} from './timeline.js';
import {
    loadActivityDetail
} from './activity.js';
import {
    initMap, renderMap, toggleMapFullscreen
} from './map.js';
import {
    updateFilterFocus, animateTransition, switchContentState
} from './ui.js';
import {
    loadGraphs, setupGraphTabs, resetGraphTabs, bindGraphInteraction, updateGraphSelection
} from './graphs.js';

const DOM = {
    startInput: document.getElementById("start-date"),
    endInput: document.getElementById("end-date"),
    presetFilter: document.querySelectorAll(".preset-filter button"),
    activityDetailContainer: document.getElementById("activity-detail-content"),
    activityTitle: document.getElementById("activity-title"),
    activityButtons: document.querySelectorAll(".activity-btn"),
    statsDateRange: document.getElementById("stats-date-range")
};

const state = {
    selectedTypes: ["run", "walk"],
    currentSelectedDate: null,
    map: null
};

document.addEventListener("DOMContentLoaded", () => {
    initUI();
    initEventListeners();

    // Initial Load
    const initialStart = document.body.dataset.start;
    const initialEnd = document.body.dataset.end;
    DOM.startInput.value = initialStart;
    DOM.endInput.value = initialEnd;

    loadAll(initialStart, initialEnd);

});

function initUI() {
    // 1. Initialize the map
    state.map = initMap('activity-map');

    // 2. Highlight the "All" filter button by default
    const allBtn = document.querySelector('[data-range="all"]');
    if (allBtn) {
        allBtn.classList.add("active");
    }
}

function initEventListeners() {
    DOM.startInput.addEventListener("change", () => loadAll(DOM.startInput.value, DOM.endInput.value));
    DOM.endInput.addEventListener("change", () => loadAll(DOM.startInput.value, DOM.endInput.value));

    DOM.startInput.addEventListener("change", () => {
        // Pass your DOM elements as arguments
        updateFilterFocus(DOM.presetFilter, DOM.startInput, DOM.endInput, DOM.startInput);
        DOM.endInput.classList.add("active"); // Optional: visual sync for end input
        loadAll(DOM.startInput.value, DOM.endInput.value);
    });

    DOM.endInput.addEventListener("change", () => {
        updateFilterFocus(DOM.presetFilter, DOM.startInput, DOM.endInput, DOM.endInput);
        DOM.startInput.classList.add("active");
        loadAll(DOM.startInput.value, DOM.endInput.value);
    });

    const expandBtn = document.getElementById('map-expand-btn');
    const mapWrapper = document.getElementById('map-wrapper');
    const mapDock = document.getElementById('map-dock');

    expandBtn.addEventListener('click', () => {
        const isOpening = !mapWrapper.classList.contains('fullscreen');

        if (isOpening) {
            mapWrapper.classList.add('fullscreen');
            document.body.appendChild(mapWrapper); // Move to body to go "over" everything
            expandBtn.innerHTML = "✕";
        } else {
            mapWrapper.classList.remove('fullscreen');
            mapDock.appendChild(mapWrapper); // Move back to the "parking spot"
            expandBtn.innerHTML = "⤢";
        }

        // Give Leaflet a moment to realize the size changed
        setTimeout(() => {
            if (state.map) state.map.invalidateSize();
        }, 100);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape" && mapWrapper.classList.contains('fullscreen')) {
            expandBtn.click(); 
        }
    });

    setupPresetFilters();
    setupActivityButtons();
    setupGraphTabs();
}

function setupPresetFilters() {
    DOM.presetFilter.forEach(btn => {
        btn.addEventListener("click", () => {
            updateFilterFocus(DOM.presetFilter, DOM.startInput, DOM.endInput, btn);
            DOM.presetFilter.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            const range = btn.dataset.range;

            // Use a new date object for "today"
            const now = new Date();
            const end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            let start = new Date(now.getFullYear(), now.getMonth(), now.getDate());

            if (range === "all") {
                start = new Date(document.body.dataset.start);
            } else {
                start.setDate(end.getDate() - parseInt(range));
            }

            DOM.startInput.value = formatDate(start);
            DOM.endInput.value = formatDate(end);
            loadAll(DOM.startInput.value, DOM.endInput.value);
        });
    });
}

function setupActivityButtons() {
    DOM.activityButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.type;

            // Toggle 'active' class on the button
            btn.classList.toggle("active");

            // Update the selectedTypes array
            if (btn.classList.contains("active")) {
                if (!state.selectedTypes.includes(type)) state.selectedTypes.push(type);
            } else {
                state.selectedTypes = state.selectedTypes.filter(t => t !== type);
            }

            // Reload the dashboard with the new filter
            loadAll(DOM.startInput.value, DOM.endInput.value);
        });
    });
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function selectDate(dateStr, element = null) {
    const types = state.selectedTypes.join(",");

    if (state.currentSelectedDate === dateStr) {
        // Deselect
        state.currentSelectedDate = null;
        resetDaySelection();
        updateGraphSelection(null);
        loadActivityDetail(
            { start: DOM.startInput.value, end: DOM.endInput.value, mode: 'latest', types: types },
            DOM.activityDetailContainer,
            DOM.activityTitle,
            state.map
        );
    } else {
        // Select
        state.currentSelectedDate = dateStr;
        setActiveDay(dateStr, element);
        updateGraphSelection(dateStr);
        loadActivityDetail(
            { start: DOM.startInput.value, end: DOM.endInput.value, mode: 'date', date: dateStr, types: types },
            DOM.activityDetailContainer,
            DOM.activityTitle,
            state.map
        );
    }
}

function loadAll(start, end) {
    state.currentSelectedDate = null;
    updateGraphSelection(null);
    resetGraphTabs();
    // Apply the fade effect to the main data containers
    animateTransition("activity-detail-content");
    animateTransition("timeline-grid");

    // For the stats, you can target the container
    const statsContainer = document.querySelector(".stats-items");
    if (statsContainer) {
        statsContainer.classList.remove("fade-in");
        void statsContainer.offsetWidth;
        statsContainer.classList.add("fade-in");
    }

    const types = state.selectedTypes.join(",");

    loadStats(start, end, types);
    updateStatsDateRange("stats-date-range", start, end);
    loadTimeline(start, end, types, selectDate);

    loadActivityDetail(
        { start, end, mode: 'latest', types },
        DOM.activityDetailContainer,
        DOM.activityTitle,
        state.map
    );

    loadGraphs(start, end, types, selectDate);
}