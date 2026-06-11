import folium
from django.contrib import admin
from .models import HuntingClub, HuntLog, Harvest
from jinja2 import Template

class HarvestInline(admin.StackedInline):
    model = Harvest
    extra = 0
    fields = ('sex', 'weight_lbs', 'is_dressed', ('points_left', 'points_right'), 'notes')

class AdminMapClickCallback(folium.elements.MacroElement):
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            var clickMarker = null;

            // Listen for clicks directly on the internal Folium map instance
            {{this._parent.get_name()}}.on('click', function(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);

                // Reach out of the map iframe into the parent Django Admin document form textboxes
                if (parent.document.getElementById('id_latitude')) {
                    parent.document.getElementById('id_latitude').value = lat;
                }
                if (parent.document.getElementById('id_longitude')) {
                    parent.document.getElementById('id_longitude').value = lng;
                }

                // Drop/move a visual marker inside the map canvas frame
                if (clickMarker) {
                    {{this._parent.get_name()}}.removeLayer(clickMarker);
                }
                clickMarker = L.marker(e.latlng).addTo({{this._parent.get_name()}});
            });
        {% endmacro %}
    """)

@admin.register(HuntLog)
class HuntLogAdmin(admin.ModelAdmin):
    list_display = ('location_zone', 'user', 'start_time', 'harvest')

    # We remove the external "Media" class script completely since the logic
    # is now packed directly inside the map engine execution thread block!

    def render_change_form(self, request, context, add=False, change=False, form_url='', MyModelForm=None):
        # 1. Build your standard baseline Folium map configuration
        # (Adjust coordinates/zoom to match your default hunting property spot)
        f_map = folium.Map(location=[33.2098, -87.5692], zoom_start=13)

        # 2. Attach our custom click cross-communication hook element to the map
        f_map.add_child(AdminMapClickCallback())

        # 3. If editing an existing log, pre-drop a marker on the recorded coords
        form_instance = context.get('adminform').form
        if form_instance.instance and form_instance.instance.latitude:
            existing_lat = form_instance.instance.latitude
            existing_lng = form_instance.instance.longitude
            folium.Marker([existing_lat, existing_lng]).add_to(f_map)
            f_map.location = [existing_lat, existing_lng]

        # 4. Export the map canvas as HTML and inject it into your admin context field rendering pipeline
        # (Make sure 'map_html' matches the custom context variable name used in your modified admin layout)
        context['map_html'] = f_map._repr_html_()

        return super().render_change_form(request, context, add, change, form_url, MyModelForm)