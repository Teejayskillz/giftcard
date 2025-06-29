from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        extra_context={'title': 'Login'}
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Registration
    path('register/', views.register, name='register'),
    
    # Wallet URLs
    path('dashboard/', views.wallet_dashboard, name='wallet_dashboard'),
    path('transactions/', views.transaction_history, name='transactions'),
    path('withdraw/', views.request_withdrawal, name='request_withdrawal'),
    path('withdraw/verify/<int:withdrawal_id>/', views.verify_withdrawal, name='verify_withdrawal'),
    path('convert/', views.convert_currency_view, name='convert_currency'),
    path('conversion-rules/', views.conversion_rules, name='conversion_rules'),
    path('conversion-rules/create/', views.create_conversion_rule, name='create_conversion_rule'),
    path('conversion-rules/<int:pk>/delete/', views.delete_conversion_rule, name='delete_conversion_rule'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
]