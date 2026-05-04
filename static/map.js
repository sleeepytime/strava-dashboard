// map.js
let map;

export function initMap(containerId) {
    map = L.map(containerId, { zoomControl: false, attributionControl: false }).setView([0, 0], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(map);
    return map;
}

export function renderMap(mapInstance, polylineData) {
    const mapContainer = document.getElementById('activity-map');
    const placeholder = document.getElementById('activity-map-placeholder');

    // 1. Check if we have any valid data to show
    const hasData = polylineData && (Array.isArray(polylineData) ? polylineData.length > 0 : true);

    if (!hasData) {
        // Hide map, show placeholder
        if (mapContainer) mapContainer.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
        return;
    }

    // 2. We have data: Show map, hide placeholder
    if (mapContainer) mapContainer.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';

    // 3. Initialize Leaflet if it hasn't been yet
    if (!map) {
        map = initMap(mapContainer)
    }

    // 4. Force refresh size (critical since we are toggling display: none)
    setTimeout(() => map.invalidateSize(), 100);

    // 5. Clear old lines
    map.eachLayer(layer => {
        if (layer instanceof L.Polyline) map.removeLayer(layer);
    });

    // 6. Draw new lines
    const polylines = Array.isArray(polylineData) ? polylineData : [polylineData];
    const bounds = L.latLngBounds();
    const decoder = window.polyline || polyline;

    polylines.forEach(str => {
        try {
            const coordinates = decoder.decode(str);
            const line = L.polyline(coordinates, {
                color: '#fc5200',
                weight: 4,
                opacity: 0.8
            }).addTo(map);
            bounds.extend(line.getBounds());
        } catch (e) {
            console.error("Map decoding failed:", e);
        }
    });

    if (bounds.isValid()) {
        map.flyToBounds(bounds, { padding: [30, 30], duration: 1.5 });
    }
}

export function toggleMapFullscreen(mapInstance) {
    const wrapper = document.getElementById('map-wrapper');
    const btnIcon = document.querySelector('#map-expand-btn .icon');
    
    wrapper.classList.toggle('fullscreen');
    
    if (wrapper.classList.contains('fullscreen')) {
        btnIcon.textContent = '✕'; // Change to X
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    } else {
        btnIcon.textContent = '⤢'; // Change back to arrows
        document.body.style.overflow = ''; // Re-enable scrolling
    }

    // Leaflet needs this to recalculate tiles for the new size
    setTimeout(() => {
        mapInstance.invalidateSize();
    }, 200); 
}