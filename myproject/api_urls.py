# main/api_urls.py
from django.urls import path
from .views import RestaurantListAPI, ReservationListCreateAPI, ReservationDetailAPI

urlpatterns = [
    path('restaurants/', RestaurantListAPI.as_view(), name='api_restaurants'),
    path('restaurants/<int:pk>/', RestaurantDetailAPI.as_view(), name='api_restaurant_detail'),
    path('reservations/', ReservationListCreateAPI.as_view(), name='api_reservations'),
    path('reservations/<int:pk>/', ReservationDetailAPI.as_view(), name='api_reservation_detail')
]
