from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.conf import settings
from django.db import models

class Profile(models.Model):
    user   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

class Restaurant(models.Model):
    favorited_by = models.ManyToManyField(
        User,
        related_name='favorite_restaurants',
        blank=True
    )
    name            = models.CharField(max_length=100)
    address         = models.CharField(max_length=255)
    address_comment = models.CharField(max_length=100, blank=True)
    phone           = models.CharField(max_length=20, blank=True)
    hours           = models.CharField(max_length=100, blank=True)
    website         = models.URLField(blank=True)
    rating          = models.FloatField(null=True, blank=True)
    purpose_name    = models.CharField(max_length=100, blank=True)
    type            = models.CharField(max_length=50, blank=True)
    is_24x7         = models.BooleanField(default=False)
    avatar_url      = models.URLField(blank=True, default='')
    lat             = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon             = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def table_count(self):
        return self.tables.count()

    @property
    def total_seats(self):
        return sum(tbl.seats for tbl in self.tables.all())

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    number     = models.PositiveIntegerField()
    seats      = models.PositiveIntegerField()

    class Meta:
        unique_together = ('restaurant', 'number')
        ordering        = ['restaurant', 'number']

    def __str__(self):
        return f"{self.restaurant.name} — стол №{self.number}"

# main/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Reservation(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    table      = models.ForeignKey('Table', on_delete=models.CASCADE, related_name='reservations')
    date       = models.DateField()
    time       = models.TimeField()        # время начала
    guests     = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['table', 'date', 'time'],
                                    name='unique_reservation')
        ]
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.user} → {self.table} @ {self.date} {self.time} ({self.guests} guests)"

class Review(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    rating     = models.PositiveSmallIntegerField()
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
