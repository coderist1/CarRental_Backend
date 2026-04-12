from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import CarDetailView, CarListCreateView, HealthCheckView, MeView, RegisterView, UserDetailView, UserListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('me/', MeView.as_view(), name='me'),
    path('users/', UserListView.as_view(), name='users-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='users-detail'),
    path('cars/', CarListCreateView.as_view(), name='cars-list-create'),
    path('cars/<int:pk>/', CarDetailView.as_view(), name='cars-detail'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
