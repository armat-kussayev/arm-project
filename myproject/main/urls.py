# main/urls.py
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',               views.home,             name='home'),
    path('about/',         views.about,            name='about'),
    path('restaurants/',   views.restaurant_list,  name='restaurant_list'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('reserve/',       views.make_reservation, name='reserve'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('cancel/<int:pk>/', views.cancel_reservation, name='cancel_reservation'),
    path('accounts/',      include('django.contrib.auth.urls')),
    path('register/',      views.register,         name='register'),
    path('api/restaurants/',  views.RestaurantListAPI.as_view(), name='api_restaurants'),
    path('api/reservations/', views.ReservationListCreateAPI.as_view(), name='api_reservations'),
    path('account/',      views.account_dashboard,  name='account_dashboard'),
    path('account/bookings/',  views.account_bookings,   name='account_bookings'),
    path('account/reviews/',   views.account_reviews,    name='account_reviews'),
    path('account/profile/',   views.account_profile,    name='account_profile'),
    path('account/favorites/', views.account_favorites,  name='account_favorites'),
    path('account/settings/',  views.account_settings,   name='account_settings'),
    path('profile/', views.profile, name='profile'),
    path('favorite/<int:pk>/', views.toggle_favorite, name='toggle_favorite'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('profile/', views.profile, name='profile'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('api/available-tables/', views.available_tables_api, name='api_available_tables'),
    path('api/update-restaurants/', views.update_restaurants, name='update_restaurants'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),

    path('api/', include('main.api_urls')),  # ← API-мостик
]
