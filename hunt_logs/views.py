from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import HuntLog

@login_required
def dashboard(request):
    """Displays a mobile-optimized index of past hunts and summary cards."""
    hunts = HuntLog.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'hunt_logs/dashboard.html', {'hunts': hunts})

@login_required
def create_hunt(request):
    """Processes or displays the mobile-friendly field-logging form."""
    if request.method == 'POST':
        # We will handle processing incoming form data here next
        pass
        
    return render(request, 'hunt_logs/create_hunt.html')
