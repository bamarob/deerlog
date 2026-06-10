import folium
from django.contrib import admin
from .models import HuntingClub, HuntLog, Harvest

class HarvestInline(admin.StackedInline):
    model = Harvest
    extra = 0
    fields = ('sex', 'weight_lbs', 'is_dressed', ('points_left', 'points_right'), 'notes')

@admin.register(HuntLog)
class HuntLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'location_zone', 'bucks_seen', 'does_seen', 'fawns_seen', 'unknown_seen', 'visibility_level')
    list_filter = ('visibility_level', 'club', 'start_time')
    search_fields = ('user__username', 'location_zone', 'notes')
    inlines = [HarvestInline]

    # --- ADD THIS METHOD TO INJECT THE MAP ---
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # Default starting point (e.g., Center of your general hunting territory)
        default_lat, default_lng = 39.8283, -98.5795
        zoom = 4

        # If editing an existing log, center the map on its saved coordinates
        if obj and obj.latitude and obj.longitude:
            default_lat = float(obj.latitude)
            default_lng = float(obj.longitude)
            zoom = 14

        # Build the mini Folium input map
        m = folium.Map(
            location=[default_lat, default_lng],
            zoom_start=zoom,
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='Map data: &copy; OpenTopoMap'
        )

        # Add a custom hidden Leaflet click event using element name naming conventions
        # We enforce an element ID of 'map_block' so our JavaScript snippet can hook into it
        m.get_root().html.add_child(folium.Element("""
            <script>
                // Expose the map object globally so our template block can find it
                window.addEventListener('DOMContentLoaded', function() {
                    var maps = Object.keys(window).filter(k => k.startsWith('map_'));
                    if(maps.length > 0) {
                        window.map_block = window[maps[0]];
                    }
                });
            </script>
        """))

        # If a log already exists, place a marker down showing where it lives
        if obj and obj.latitude and obj.longitude:
            folium.Marker([default_lat, default_lng], icon=folium.Icon(color='red')).add_to(m)

        # Render out the raw map code and push it into the page context
        context['admin_map_html'] = m._repr_html_()
        
        return super().render_change_form(request, context, add, change, form_url, obj)
