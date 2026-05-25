from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import HuntLog
import folium

def map_dashboard(request):
    """The original administrative overview map view."""
    hunts = HuntLog.objects.filter(user=request.user)
    
    # Default fallback map center if no hunt logs exist yet
    start_lat, start_lng = 33.905783, -87.729952
    zoom_level = 14
    
    if hunts.exists():
        latest_hunt = hunts.latest('start_time')
        start_lat = float(latest_hunt.latitude)
        start_lng = float(latest_hunt.longitude)

    m = folium.Map(
        location=[start_lat, start_lng], 
        zoom_start=zoom_level,
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: &copy; OpenTopoMap contributors'
    )

    for hunt in hunts:
        popup_text = f"""
        <strong>Zone:</strong> {hunt.location_zone or 'Unmarked Stand'}<br>
        <strong>Date:</strong> {hunt.start_time.strftime('%b %d, %Y')}<br>
        <strong>Deer Seen:</strong> {hunt.total_deer_seen} (B: {hunt.bucks_seen}, D: {hunt.does_seen})<br>
        """
        
        has_harvest = hasattr(hunt, 'harvest')
        if has_harvest:
            harvest = hunt.harvest
            popup_text += f"🏁 <strong>Harvested:</strong> {harvest.sex} ({int(harvest.weight_lbs)} lbs)"
            if harvest.sex == 'Buck':
                popup_text += f" - {harvest.total_points} pt!"
            marker_icon = folium.Icon(color='red', icon='trophy', prefix='fa')
        else:
            marker_icon = folium.Icon(color='green', icon='eye', prefix='fa')

        folium.Marker(
            location=[float(hunt.latitude), float(hunt.longitude)],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{hunt.start_time.strftime('%m/%d')} Log - Click for Details",
            icon=marker_icon
        ).add_to(m)

    map_html = m._repr_html_()
    return render(request, 'hunt_logs/map_dashboard.html', {'map_html': map_html})


# --- NEW FRONTEND VIEWS ---

@login_required
def dashboard(request):
    """Displays a mobile-optimized index of past hunts and summary cards."""
    hunts = HuntLog.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'hunt_logs/dashboard.html', {'hunts': hunts})

@login_required
def create_hunt(request):
    """Processes or displays the mobile-friendly field-logging form."""
    if request.method == 'POST':
        pass
        
    return render(request, 'hunt_logs/create_hunt.html')
