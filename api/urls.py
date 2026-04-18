from django.urls import path

from .views import (
    BookingDetailView,
    BookingListCreateView,
    CarDetailView,
    CarListCreateView,
    EmailLogDetailView,
    EmailLogListCreateView,
    HealthCheckView,
    LogReportDetailView,
    LogReportListCreateView,
    MeView,
    LoginView,
    PasswordChangeView,
    PasswordResetView,
    RegisterView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/', PasswordResetView.as_view(), name='password-reset'),
    path('me/', MeView.as_view(), name='me'),
    path('bookings/', BookingListCreateView.as_view(), name='bookings-list-create'),
    path('bookings/<int:pk>/', BookingDetailView.as_view(), name='bookings-detail'),
    path('log-reports/', LogReportListCreateView.as_view(), name='log-reports-list-create'),
    path('log-reports/<int:pk>/', LogReportDetailView.as_view(), name='log-reports-detail'),
    path('email-logs/', EmailLogListCreateView.as_view(), name='email-logs-list-create'),
    path('email-logs/<int:pk>/', EmailLogDetailView.as_view(), name='email-logs-detail'),
    path('users/', UserListView.as_view(), name='users-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='users-detail'),
    path('cars/', CarListCreateView.as_view(), name='cars-list-create'),
    path('cars/<int:pk>/', CarDetailView.as_view(), name='cars-detail'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
