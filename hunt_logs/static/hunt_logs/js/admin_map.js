console.log("DeerLog script loaded successfully!");

function attachMapClickListener(adminMap) {
    console.log("Found the Leaflet map instance! Attaching listeners...");
    
    var latInput = document.getElementById('id_latitude');
    var lngInput = document.getElementById('id_longitude');
    
    // Initialize our tracking marker as null
    window.adminClickMarker = null;

    adminMap.on('click', function(event) {
        console.log("Map clicked at:", event.latlng);
        if (latInput && lngInput) {
            latInput.value = event.latlng.lat.toFixed(6);
            lngInput.value = event.latlng.lng.toFixed(6);
        }
        
        if (window.adminClickMarker) {
            adminMap.removeLayer(window.adminClickMarker);
        }
        
        window.adminClickMarker = L.marker(event.latlng, {draggable: true}).addTo(adminMap);
        
        window.adminClickMarker.on('dragend', function(dragEvent) {
            var position = window.adminClickMarker.getLatLng();
            if (latInput && lngInput) {
                latInput.value = position.lat.toFixed(6);
                lngInput.value = position.lng.toFixed(6);
            }
        });
    });

    // Handle existing coordinates on edit forms
    if (latInput && lngInput && latInput.value && lngInput.value) {
        var existingLoc = [parseFloat(latInput.value), parseFloat(lngInput.value)];
        window.adminClickMarker = L.marker(existingLoc, {draggable: true}).addTo(adminMap);
        adminMap.setView(existingLoc, 14);
    }
}

// Strategy 1: Try Django-Leaflet's native event wrapper
window.addEventListener('map:init', function (e) {
    attachMapClickListener(e.detail.map);
});

// Strategy 2: Fallback poll loop in case the event already fired
window.addEventListener('load', function() {
    setTimeout(function() {
        if (!window.adminClickMarker) {
            // Check if a global leaflet map cache array exists
            if (typeof djangoFormGeomMySQL !== 'undefined' && djangoFormGeomMySQL.maps && djangoFormGeomMySQL.maps[0]) {
                attachMapClickListener(djangoFormGeomMySQL.maps[0]);
            } else if (typeof window.django_leaflet_maps !== 'undefined' && window.django_leaflet_maps[0]) {
                attachMapClickListener(window.django_leaflet_maps[0]);
            } else {
                // Last ditch effort: scan the page for any raw leaflet map elements
                var mapElements = document.querySelectorAll('.leaflet-container');
                if (mapElements.length > 0) {
                    console.log("Leaflet container found, attempting to force map extraction...");
                    // Try to extract the map from internal Leaflet storage keys
                    for (var i = 0; i < mapElements.length; i++) {
                        var el = mapElements[i];
                        if (el._leaflet_id && el.leaflet_map) attachMapClickListener(el.leaflet_map);
                    }
                }
            }
        }
    }, 1000); // Give the DOM 1 full second to settle down
});