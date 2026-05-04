// graph.js
import { switchContentState } from "./ui.js";

// Initialize the tabs logic
export function setupGraphTabs() {
    document.querySelectorAll(".tab").forEach(tab => {
        tab.addEventListener("click", () => {
            // 1. Update active tab styling
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const target = tab.dataset.graph; // 'miles' or 'pace'
            const container = document.getElementById("graph-empty");

            // 2. Data-Aware Toggle
            // Check if the placeholder is currently showing (meaning no data)
            if (container.style.display === 'flex') {
                // If empty, keep charts hidden
                document.getElementById("mile_chart").style.display = 'none';
                document.getElementById("pace_chart").style.display = 'none';
            } else {
                // Only show the target chart if we have data
                document.getElementById("mile_chart").style.display = target === "miles" ? "block" : "none";
                document.getElementById("pace_chart").style.display = target === "pace" ? "block" : "none";
            }

            // Trigger resize so Plotly refreshes the viewport
            window.dispatchEvent(new Event("resize"));
        });
    });
}

// Reset graph tabs to default state
export function resetGraphTabs() {
    const tabs = document.querySelectorAll(".tab");
    tabs.forEach(t => t.classList.remove("active"));

    // Set "Distance" tab as active
    const distanceTab = document.querySelector('[data-graph="miles"]');
    if (distanceTab) distanceTab.classList.add("active");

    // Ensure the Distance chart is visible and Pace is hidden
    document.getElementById("mile_chart").style.display = 'block';
    document.getElementById("pace_chart").style.display = 'none';
}

// Bind Plotly interaction
export function bindGraphInteraction(chartId, onDayClick) {
    const chart = document.getElementById(chartId);
    chart.removeAllListeners('plotly_click');

    chart.on('plotly_click', function (data) {
        if (data.points && data.points.length > 0 && data.points[0].curveNumber === 1) {
            onDayClick(data.points[0].x);
        }
    });
}

// Update graph selection highlighting
export function updateGraphSelection(dateStr) {
    ["mile_chart", "pace_chart"].forEach(id => {
        const chartDiv = document.getElementById(id);
        if (!chartDiv || !chartDiv.data) return;

        if (dateStr === null) {
            // 1. Reset: Return Trendline (Trace 0) to full opacity
            Plotly.restyle(id, { 'opacity': 1 }, [0]);
            // 2. Reset: Clear selection on Dots (Trace 1)
            Plotly.restyle(id, { 'selectedpoints': [null] }, [1]);
            return;
        }

        // We look at Trace 1 (the raw activity dots)
        const xValues = chartDiv.data[1].x;
        const idx = xValues.indexOf(dateStr);

        if (idx !== -1) {
            // 1. Dim the Trendline (Trace 0)
            Plotly.restyle(id, { 'opacity': 0.2 }, [0]);

            // 2. Highlight the specific dot in Trace 1
            // Plotly will automatically dim the OTHER dots in this trace
            Plotly.restyle(id, { 'selectedpoints': [[idx]] }, [1]);
        }
    });
}


export async function loadGraphs(start, end, types, onDayClick) {
    try {
        const res = await fetch(`/update_graphs?start=${start}&end=${end}&types=${types}`);
        const data = await res.json();
        const hasData = data.mile_chart.data?.length > 0

        // Toggle Graphs
        switchContentState("mile_chart", "graph-empty", hasData);
        // Note: Also hide pace_chart if no data
        document.getElementById("pace_chart").style.display = 'none';

        if (hasData) {
            const config = { responsive: true, displayModeBar: true };
            Plotly.newPlot("mile_chart", data.mile_chart.data, data.mile_chart.layout, config);
            Plotly.newPlot("pace_chart", data.pace_chart.data, data.pace_chart.layout, config);

            bindGraphInteraction("mile_chart", onDayClick);
            bindGraphInteraction("pace_chart", onDayClick);
        }
    } catch (err)
    {
        console.error("Failed to load graphs:", err);
    }
}
