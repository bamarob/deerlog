from django.db import models
from django.contrib.auth.models import User

class HuntingClub(models.Model):
    name = models.CharField(max_length=200, help_text="The name of the hunting club or lease.")
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_clubs")
    join_code = models.CharField(max_length=12, unique=True, help_text="Unique code for members to join.")

    def __str__(self):
        return self.name


class HuntLog(models.Model):
    # Privacy / Visibility levels
    VISIBILITY_CHOICES = [
        (0, 'Private (Only Me)'),
        (1, 'Masked/Aggregated (Hide Location)'),
        (2, 'Full Club (Share Everything)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hunt_logs")
    club = models.ForeignKey(HuntingClub, on_delete=models.SET_NULL, null=True, blank=True, related_name="club_hunts")
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Baseline Location (SQLite compatible, easily migratable to PostGIS later)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_zone = models.CharField(max_length=100, blank=True, help_text="General area e.g., 'North Ridge' or 'Stand 4'")
    
    # Deer Sighting Counts
    bucks_seen = models.IntegerField(default=0)
    does_seen = models.IntegerField(default=0)
    fawns_seen = models.IntegerField(default=0)
    unknown_seen = models.IntegerField(default=0)
    
    visibility_level = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)
    notes = models.TextField(blank=True, help_text="General observations (weather, wind, sign, acorns, etc.)")

    @property
    def total_deer_seen(self):
        """Calculates total deer activity for dashboard reporting."""
        return self.bucks_seen + self.does_seen + self.fawns_seen + self.unknown_seen

    def __str__(self):
        return f"{self.user.username}'s Hunt on {self.start_time.strftime('%Y-%m-%d')}"


class Harvest(models.Model):
    SEX_CHOICES = [
        ('Buck', 'Buck'),
        ('Doe', 'Doe'),
    ]
    
    # One-to-One relationship creates a true 'Child Record'
    # If a Hunt Log is deleted, its matching Harvest record is wiped out too.
    hunt = models.OneToOneField(HuntLog, on_delete=models.CASCADE, related_name="harvest")
    
    sex = models.CharField(max_length=10, choices=SEX_CHOICES)
    weight_lbs = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in pounds")
    is_dressed = models.BooleanField(default=False, verbose_name="Field Dressed?")
    
    # Antler data (Only populated if sex == 'Buck')
    points_left = models.IntegerField(default=0, blank=True)
    points_right = models.IntegerField(default=0, blank=True)
    
    notes = models.TextField(blank=True, help_text="Shot placement, recovery tracking details, etc.")

    @property
    def total_points(self):
        """Calculates total antler points dynamically."""
        if self.sex == 'Buck':
            return self.points_left + self.points_right
        return 0

    def __str__(self):
        return f"{self.sex} harvested during {self.hunt}"
