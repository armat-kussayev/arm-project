from django.contrib import admin
from .models import Restaurant, Table, Reservation, Review


try:
    admin.site.unregister(Restaurant)
except admin.sites.NotRegistered:
    pass

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display   = ('name', 'address', 'phone', 'hours', 'rating', 'table_count', 'total_seats')
    search_fields  = ('name', 'address')
    list_per_page  = 25

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display  = ('restaurant', 'number', 'seats')
    list_filter   = ('restaurant',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display    = ('user', 'table', 'date', 'time', 'created_at')
    list_filter     = ('date',)
    date_hierarchy  = 'date'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display   = ('restaurant', 'user', 'rating', 'created_at')
    list_filter    = ('rating', 'created_at')
