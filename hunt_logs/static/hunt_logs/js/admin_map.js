// Wait for the admin page DOM container to fully allocate resources
window.addEventListener('load', function() {
    // Look up Django's native auto-generated admin text input form wrappers
    var latInput = document.getElementById('id_latitude');
    var lngInput = document.getElementById('id_longitude');

    // Find the Leaflet map container instances drawn inside the administration pane
    // Using a minor delay ensures Leaflet has initialized its active window binds
    setTimeout(function() {
        if (typeof map !== 'undefined') {

            // Map click listener hook
            map.on('click', function(e) {
                if (latInput && lngInput) {
                    latInput.value = e.latlng.lat.toFixed(6);
                    lngInput.value = e.latlng.lng.toFixed(6);
                }

                // If a draggable marker exists, sync its position to the click coordinate
                if (typeof marker !== 'undefined') {
                    marker.setLatLng(e.latlng);
                }
            });

            // Draggable marker listener hook
            if (typeof marker !== 'undefined') {
                marker.on('dragend', function(e) {
                    var position = marker.getLatLng();
                    if (latInput && lngInput) {
                        latInput.value = position.lat.toFixed(6);
                        lngInput.value = position.lng.toFixed(6);
                    }
                });
            }
        }
    }, 600);
});