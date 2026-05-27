from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import HuntLog
from .models import Harvest
import folium

@login_required
def map_dashboard(request):
    """1. The administrative topographic map view."""
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


@login_required
def dashboard(request):
    """2. The mobile-optimized landing page history index."""
    hunts = HuntLog.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'hunt_logs/dashboard.html', {'hunts': hunts})


@login_required
def create_hunt(request):
    """3. Processes and saves the mobile field-logging form data."""
    if request.method == 'POST':
        location_zone = request.POST.get('location_zone')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        bucks_seen = request.POST.get('bucks_seen', 0)
        does_seen = request.POST.get('does_seen', 0)
        fawns_seen = request.POST.get('fawns_seen, 0)
        unknwon_seen = request.POST.get('unknown_seen, 0)
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
            bucks_seen=int(bucks_seen),
            does_seen=int(does_seen),
            fawns_seen=int(fawns_seen),
            unknown_seen=int(unknown_seen)
            visibility_level=visibility_level,
            notes=notes
        )
        new_log.save()
        return redirect('dashboard')
        
    return render(request, 'hunt_logs/create_hunt.html')

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
