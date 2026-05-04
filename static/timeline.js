// timeline.js
export function renderTimeline(months, onDayClick) {
    const timelineGrid = document.getElementById("timeline-grid");
    timelineGrid.innerHTML = ""; // Clear existing grid

    months.forEach(month => {
        // Create Month Label
        const label = document.createElement("div");
        label.className = "month-label";
        label.textContent = month.label;
        label.style.gridColumn = "1 / span 7";
        timelineGrid.appendChild(label);

        // Loop through Days
        month.days.forEach((day, index) => {
            const dayBox = document.createElement("div");
            dayBox.className = `day intensity-${day.intensity}`;
            dayBox.textContent = day.day;
            dayBox.setAttribute("data-date", day.date);
            dayBox.setAttribute("data-tooltip", day.tooltip);

            if (index === 0) dayBox.style.gridColumnStart = day.weekday + 1;

            // Determine if the day has activity
            const hasActivity = day.intensity > 0;

            // Trigger the passed callback when clicked
            dayBox.addEventListener("click", () => onDayClick(day.date, dayBox, hasActivity));

            timelineGrid.appendChild(dayBox);
        });
    });
}

export async function loadTimeline(start, end, types, onDayClick) {
    try{
        const res = await fetch(`/api/timeline?start=${start}&end=${end}&types=${types}`);
        const months = await res.json();
        renderTimeline(months, onDayClick)

    } catch (err) {
        console.error("Failed to load timeline:", err)
    };
}

export function setActiveDay(dateStr, element = null) {
    document.querySelectorAll(".day").forEach(d => d.classList.remove("active-day"));
    const target = element || document.querySelector(`.day[data-date="${dateStr}"]`);
    if (target) {
        target.classList.add("active-day");
        const container = document.querySelector('.timeline-container');
        container.scrollTo({
            top: target.offsetTop - (container.offsetHeight / 2),
            behavior: 'smooth'
        });
    }
}

export function resetDaySelection() {
    document.querySelectorAll(".day").forEach(d => d.classList.remove("active-day"));
}