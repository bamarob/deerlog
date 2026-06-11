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
            {{this._parent.get_name()}}.on('click', function(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);

                if (parent.document.getElementById('id_latitude')) {
                    parent.document.getElementById('id_latitude').value = lat;
                }
                if (parent.document.getElementById('id_longitude')) {
                    parent.document.getElementById('id_longitude').value = lng;
                }

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

    # Using *args and **kwargs makes this bulletproof across all Django versions
    def render_change_form(self, request, context, *args, **kwargs):
        # 1. Set up the default Folium map configuration
        f_map = folium.Map(location=[33.2098, -87.5692], zoom_start=13)

        # 2. Attach our custom iframe escape click callback
        f_map.add_child(AdminMapClickCallback())

        # 3. Check for existing coordinates if editing an entry
        form_instance = context.get('adminform').form
        if form_instance.instance and getattr(form_instance.instance, 'latitude', None):
            existing_lat = form_instance.instance.latitude
            existing_lng = form_instance.instance.longitude
            folium.Marker([existing_lat, existing_lng]).add_to(f_map)
            f_map.location = [existing_lat, existing_lng]

        # 4. Pass the map HTML to the admin context template
        context['map_html'] = f_map._repr_html_()

        # Pass everything smoothly back up to the native Django layout engine
        return super().render_change_form(request, context, *args, **kwargs)