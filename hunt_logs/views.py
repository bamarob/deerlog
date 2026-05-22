from django.shortcuts import render
from .models import HuntLog
import folium

def map_dashboard(request):
    # 1. Fetch all hunt logs belonging to the user from SQLite
    hunts = HuntLog.objects.filter(user=request.user)
    
    # Default fallback map center if no hunt logs exist yet (e.g., Center of US)
    start_lat, start_lng = 33.905783, -87.729952 
    zoom_level = 12
    
    if hunts.exists():
        # Center the map on the hunter's most recent outing
        latest_hunt = hunts.latest('start_time')
        start_lat = float(latest_hunt.latitude)
        start_lng = float(latest_hunt.longitude)
        zoom_level = 13  # Zoomed in closer for local stand visibility

    # 2. Initialize the Folium Map using Topographic/Outdoor friendly tiles
    # OpenTopoMap provides excellent elevation contours and tree cover visuals
    m = folium.Map(
        location=[start_lat, start_lng], 
        zoom_start=zoom_level,
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: &copy; OpenTopoMap contributors'
    )

    # 3. Iterate over the logs and plot data markers dynamically
    for hunt in hunts:
        # Build out text details for map popups
        popup_text = f"""
        <strong>Zone:</strong> {hunt.location_zone or 'Unmarked Stand'}<br>
        <strong>Date:</strong> {hunt.start_time.strftime('%b %d, %Y')}<br>
        <strong>Deer Seen:</strong> {hunt.total_deer_seen} (B: {hunt.bucks_seen}, D: {hunt.does_seen})<br>
        """
        
        # Check if our One-to-One Child Harvest record exists for this specific hunt session
        has_harvest = hasattr(hunt, 'harvest')
        
        if has_harvest:
            harvest = hunt.harvest
            popup_text += f"🏁 <strong>Harvested:</strong> {harvest.sex} ({int(harvest.weight_lbs)} lbs)"
            if harvest.sex == 'Buck':
                popup_text += f" - {harvest.total_points} pt!"
            
            # Use a striking red marker icon to identify successful harvest fields
            marker_icon = folium.Icon(color='red', icon='trophy', prefix='fa')
        else:
            # Use a standard green marker configuration for generic observation logs
            marker_icon = folium.Icon(color='green', icon='eye', prefix='fa')

        # Add the physical coordinate layer marker onto our base map object
        folium.Marker(
            location=[float(hunt.latitude), float(hunt.longitude)],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{hunt.start_time.strftime('%m/%d')} Log - Click for Details",
            icon=marker_icon
        ).add_to(m)

    # 4. Render the internal map structure out to standard HTML
    map_html = m._repr_html_()

    # Pass the compiled map string object directly to our frontend dashboard template context
    return render(request, 'hunt_logs/map_dashboard.html', {'map_html': map_html})
