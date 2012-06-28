from django.db import models

class Shuttle(models.Model):
    name = models.CharField(max_length=10)
    last_stop = models.CharField(max_length=35, blank=True, null=True)
    east_west = models.CharField(max_length=4, blank=True, null=True)
    current_lat = models.DecimalField(max_digits=16, decimal_places=13, blank=True, null=True)
    current_long = models.DecimalField(max_digits=16, decimal_places=13, blank=True, null=True)
    active = models.BooleanField()
    updated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
class ShuttleStop(models.Model):
    name = models.CharField(max_length=35)
    latitude = models.DecimalField(max_digits=16, decimal_places=13)
    longitude = models.DecimalField(max_digits=16, decimal_places=13)

    def __str__(self):
        return self.name

class RouteCoordinate(models.Model):
    latitude = models.DecimalField(max_digits=16, decimal_places=13)
    longitude = models.DecimalField(max_digits=16, decimal_places=13)
    last_loc = models.IntegerField()
    east_west = models.CharField(max_length=5)

    def __str__(self):
        return str(self.last_stop) + " -- " + str(self.latitude) + ", " + str(self.longitude)

