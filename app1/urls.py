from django.urls import path
from . import views

urlpatterns = [
    # Core & Navigation
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Core Farming Modules
    path('government-schemes/', views.government_schemes, name='government_schemes'),
    path('weather/', views.weather, name='weather'),
    path('crop-advisory/', views.crop_advisory, name='crop_advisory'),
    path('fertilizer/', views.fertilizer, name='fertilizer'),
    path('compost/', views.compost, name='compost'),
    path('market-price/', views.market_price, name='market_price'),

    # Notifications Module
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Dynamic Location AJAX Endpoints
    path('ajax/load-districts/', views.load_districts, name='ajax_load_districts'),
    path('ajax/load-talukas/', views.load_talukas, name='ajax_load_talukas'),
]