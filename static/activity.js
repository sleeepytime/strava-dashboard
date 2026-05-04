// activity.js
import { fetchData } from './api.js';
import { renderMap } from './map.js';
import { renderStat } from './stats.js';
import { animateTransition, switchContentState } from './ui.js';

export async function loadActivityDetail(params, container, titleEl, mapInstance) {
    // 1. Maintain the original animation trigger
    animateTransition("activity-detail-content");

    const data = await fetchData('/activity_detail', params);
    const hasData = data.exists && data.activities.length > 0;

    // 2. Maintain both content AND map state toggles
    switchContentState("activity-detail-content", "activity-empty", hasData);
    switchContentState("activity-map", "activity-map-placeholder", hasData);

    // 3. Early Exit for "No Data" state
    if (!hasData) {
        titleEl.textContent = params.date ? `No activity on ${params.date}` : "No activity";
        container.innerHTML = "<p>No activity recorded.</p>";
        renderMap(mapInstance, null);
        return;
    }

    // 4. Happy Path: Render content
    const count = data.activities.length;
    titleEl.textContent = `${count} ${count === 1 ? "activity" : "activities"} on ${data.date}`;
    container.innerHTML = data.activities.map(renderActivityCard).join("");

    // 5. Maintain the original polyline filtering logic
    const allPolylines = data.activities
        .map(a => a.summary_polyline)
        .filter(p => p && p !== "" && p !== "nan");
        
    renderMap(mapInstance, allPolylines);
}

export function renderActivityCard(a) {
    return `
        <div class="activity-card activity-item">
            <div class="activity-header">
                <div class="activity-name">${a.name}</div>
                <div class="activity-meta">${a.date} • ${a.time} • ${a.type}</div>
            </div>

            <div class="activity-main">
                ${renderStat(a.distance, "Miles")}
                ${renderStat(a.pace, "Pace")}
                ${renderStat(a.moving_time, "Time")}
            </div>

            <div class="activity-secondary">
                Elevation: ${a.elevation} ft
            </div>

            <div class="activity-context">
                Month: ${a.month_total} mi • Total: ${a.total_miles} mi
            </div>
        </div>
    `;
}