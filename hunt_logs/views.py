from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import HuntLog
from .models import Harvest
from django.db.models import Sum
import folium
from jinja2 import Template

# ==========================================
# FOLIUM IFRAME ESCAPE MACRO
# ==========================================
class FrontendMapClickCallback(folium.elements.MacroElement):
    """
    Custom Folium macro that injects a JavaScript click event inside the map iframe.
    It catches the click coordinates and pushes them out into the parent Django 
    HTML form's 'id_latitude' and 'id_longitude' input textboxes.
    """
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            var clickMarker = null;
            {{this._parent.get_name()}}.on('click', function(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);
                
                // Reach past the iframe window boundary directly into the frontend form fields
                if (parent.document.getElementById('id_latitude')) {
                    parent.document.getElementById('id_latitude').value = lat;
                }
                if (parent.document.getElementById('id_longitude')) {
                    parent.document.getElementById('id_longitude').value = lng;
                }
                
                // Drop a visual pin on the spot clicked, clearing any old click pins first
                if (clickMarker) {
                    {{this._parent.get_name()}}.removeLayer(clickMarker);
                }
                clickMarker = L.marker(e.latlng).addTo({{this._parent.get_name()}});
            });
        {% endmacro %}
    """)


# ==========================================
# MAP DASHBOARD VIEW
# ==========================================
@login_required
def map_dashboard(request):
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
        zone = hunt.location_zone or "Unmarked Stand"
        date_str = hunt.start_time.strftime('%b %d, %Y')
        b = hunt.bucks_seen
        d = hunt.does_seen
        f = hunt.fawns_seen
        u = hunt.unknown_seen
        total = b + d + f + u

        popup_text = f"""
        <strong>Zone:</strong> {zone}<br>
        <strong>Date:</strong> {date_str}<br>
        <strong>Deer Seen:</strong> {total} (B: {b}, D: {d}, F: {f}, U: {u})<br>
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


# ==========================================
# HISTORY DASHBOARD INDEX VIEW
# ==========================================
@login_required
def dashboard(request):
    """2. The mobile-optimized landing page history index."""
    hunts = HuntLog.objects.filter(user=request.user).order_by('-start_time')

    amounts = hunts.aggregate(
            total_bucks=Sum('bucks_seen'),
            total_does=Sum('does_seen'),
            total_fawns=Sum('fawns_seen'),
            total_unknown=Sum('unknown_seen'),
            total_harvested=Sum('harvest')
    )

    b = amounts['total_bucks'] or 0
    d = amounts['total_does'] or 0
    f = amounts['total_fawns'] or 0
    u = amounts['total_unknown'] or 0

    grand_total_seen = b + d + f + u

    # Catch a None value for harvest and turn it into 0
    grand_total_harvest = amounts['total_harvested'] or 0

    context = {
            'hunts': hunts,
            'total_deer_seen_count': grand_total_seen,
            'total_harvest_count': grand_total_harvest,
    }

    return render(request, 'hunt_logs/dashboard.html', context)


# ==========================================
# FIELD ENTRY CREATE VIEW
# ==========================================
@login_required
def create_hunt(request):
    """3. Processes and saves the mobile field-logging form data with interactive Folium canvas."""
    if request.method == 'POST':
        location_zone = request.POST.get('location_zone')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        bucks = request.POST.get('bucks', 0)
        does = request.POST.get('does', 0)
        fawns = request.POST.get('fawns', 0)
        unknown = request.POST.get('unknown', 0)

        start_str = request.POST.get('start_time')
        end_str = request.POST.get('end_time')
        start_dt = parse_datetime(start_str) if start_str else None
        end_dt = parse_datetime(end_str) if end_str else None
        visibility_level = request.POST.get('visibility_level')
        notes = request.POST.get('notes')

        new_log = HuntLog(
            user=request.user,
            start_time=start_dt,
            end_time=end_dt,
            location_zone=location_zone,
            latitude=float(latitude) if latitude else 0.0,
            longitude=float(longitude) if longitude else 0.0,
            bucks_seen=int(bucks) if bucks else 0,
            does_seen=int(does) if does else 0,
            fawns_seen=int(fawns) if fawns else 0,
            unknown_seen=int(unknown) if unknown else 0,
            visibility_level=visibility_level,
            notes=notes
        )
        new_log.save()
        return redirect('dashboard')

    # --- GET Request Configuration: Build the Folium Form Map Pipeline ---
    # Match your preferred topo-map layer style, defaulting center near previous hunts
    hunts = HuntLog.objects.filter(user=request.user)
    start_lat, start_lng = 33.905783, -87.729952
    
    if hunts.exists():
        latest_hunt = hunts.latest('start_time')
        start_lat = float(latest_hunt.latitude)
        start_lng = float(latest_hunt.longitude)

    m = folium.Map(
        location=[start_lat, start_lng],
        zoom_start=14,
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='Map data: &copy; OpenTopoMap contributors'
    )
    
    # Inject our macro listener block into the map map canvas instance
    m.add_child(FrontendMapClickCallback())
    
    context = {
        'map_html': m._repr_html_()
    }
    return render(request, 'hunt_logs/create_hunt.html', context)


# ==========================================
# HARVEST SUBMISSION VIEW
# ==========================================
@login_required
def create_harvest(request, hunt_id):
    """Processes and links a harvest entry to a specific hunt sit."""
    hunt = get_object_or_404(HuntLog, id=hunt_id, user=request.user)

    if request.method == 'POST':
        sex = request.POST.get('sex')
        weight_lbs = request.POST.get('weight_lbs')
        inside_spread = request.POST.get('inside_spread', 0.0)

        p_left = int(request.POST.get('points_left', 0))
        p_right = int(request.POST.get('points_right', 0))

        new_harvest = Harvest(
            hunt=hunt,
            sex=sex,
            weight_lbs=float(weight_lbs),
            points_left=p_left if sex == 'Buck' else 0,
            points_right=p_right if sex == 'Buck' else 0,
            inside_spread=float(inside_spread) if sex == 'Buck' else 0.0
        )
        new_harvest.save()
        return redirect('dashboard')

    return render(request, 'hunt_logs/create_harvest.html', {'hunt': hunt})