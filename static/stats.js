// stats.js
import { fetchData } from './api.js';

export async function loadStats(start, end, types) {
    try {
        const params = { start, end, types };
        const data = await fetchData('/update_stats', params);
        updateStat("total-miles", data.total_miles);
        updateStat("total-time", data.total_time);
        updateStat("total-activities", data.total_activities);
    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}

export function updateStat(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

export function updateStatsDateRange(elementId, start, end) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = `${start} – ${end}`;
    }
}

export function renderStat(value, label) {
    return `
        <div class="stat">
            <div class="stat-value">${value}</div>
            <div class="stat-label">${label}</div>
        </div>
    `;
}