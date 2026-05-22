from django.urls import path
from . import views

urlpatterns = [
    # Your original admin mapping view
    path('map/', views.map_dashboard, name='map_dashboard'),
    
    # NEW ROUTES:
    # Main user dashboard showing history and quick links
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Mobile-friendly form to log a new sit from the field
    path('create/', views.create_hunt, name='create_hunt'),
]
