// Listen globally for Django-Leaflet's native map initialization event
window.addEventListener('map:init', function (e) {
    // Grab the actual map instance straight out of the initialization detail package
    var adminMap = e.detail.map;
    
    // Locate Django Admin's exact auto-generated form input IDs
    var latInput = document.getElementById('id_latitude');
    var lngInput = document.getElementById('id_longitude');
    
    // Add a click listener directly to the admin map instance
    adminMap.on('click', function(event) {
        if (latInput && lngInput) {
            // Populate the textboxes with clean high-precision decimals
            latInput.value = event.latlng.lat.toFixed(6);
            lngInput.value = event.latlng.lng.toFixed(6);
        }
        
        // Clear any old temporary markers so they don't pile up on your admin screen
        if (window.adminClickMarker) {
            adminMap.removeLayer(window.adminClickMarker);
        }
        
        // Drop a fresh draggable marker on the exact spot you clicked
        window.adminClickMarker = L.marker(event.latlng, {draggable: true}).addTo(adminMap);
        
        // If the user drags the marker around, keep the input fields perfectly synchronized
        window.adminClickMarker.on('dragend', function(dragEvent) {
            var position = window.adminClickMarker.getLatLng();
            if (latInput && lngInput) {
                latInput.value = position.lat.toFixed(6);
                lngInput.value = position.lng.toFixed(6);
            }
        });
    });
    
    // If coordinates are already present in the form (like editing an old hunt log entry),
    // automatically pre-drop the map marker on that spot when the page finishes loading
    if (latInput && lngInput && latInput.value && lngInput.value) {
        var existingLoc = [parseFloat(latInput.value), parseFloat(lngInput.value)];
        window.adminClickMarker = L.marker(existingLoc, {draggable: true}).addTo(adminMap);
        adminMap.setView(existingLoc, 14);
    }
});