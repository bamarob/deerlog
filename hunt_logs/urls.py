from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    # Map the blank root URL directly to the dashboard
    path('', RedirectView.as_view(url='/hunts/dashboard/', permanent=True)),
    
    # Your original admin mapping view
    path('map/', views.map_dashboard, name='map_dashboard'),
    
    # NEW ROUTES:
    # Main user dashboard showing history and quick links
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Mobile-friendly form to log a new sit from the field
    path('create/', views.create_hunt, name='create_hunt'),

    # Dynamic route passing the primary key of the hunt card being clicked
    path('harvest/<int:hunt_id>/', views.create_harvest, name='create_harvest'), 
]
