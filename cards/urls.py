# cards/urls.py
from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('submit/', views.submit_card, name='submit'),
    path('submission-success/', views.submission_success, name='submission_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('withdraw/', views.withdraw_funds, name='withdraw'),
    path('api/calculate-offer/', views.calculate_offer, name='calculate_offer'),
    path('api/card-countries/', views.card_countries, name='card_countries'),
]