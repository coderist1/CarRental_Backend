from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car
from .serializers import CarSerializer, UserRegisterSerializer, UserSerializer, UserUpdateSerializer


class IsAdminUserRole(permissions.BasePermission):
	def has_permission(self, request, view):
		return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class RegisterView(generics.CreateAPIView):
	queryset = User.objects.all()
	serializer_class = UserRegisterSerializer
	permission_classes = [permissions.AllowAny]

	def perform_create(self, serializer):
		user = serializer.save()
		if getattr(user, 'profile', None) and user.profile.role == 'admin':
			user.is_staff = True
			user.save(update_fields=['is_staff'])


class MeView(APIView):
	def get(self, request):
		return Response(UserSerializer(request.user).data)

	def patch(self, request):
		serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(UserSerializer(user).data)


class UserListView(generics.ListAPIView):
	queryset = User.objects.all().select_related('profile').order_by('-date_joined')
	serializer_class = UserSerializer
	permission_classes = [IsAdminUserRole]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = User.objects.all().select_related('profile')
	serializer_class = UserUpdateSerializer
	permission_classes = [IsAdminUserRole]

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		return Response(UserSerializer(self.get_object()).data)


class CarListCreateView(generics.ListCreateAPIView):
	queryset = Car.objects.all()
	serializer_class = CarSerializer

	def get_permissions(self):
		if self.request.method == 'GET':
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		return Car.objects.select_related('owner').all()


class CarDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Car.objects.all()
	serializer_class = CarSerializer

	def get_permissions(self):
		if self.request.method == 'GET':
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		return Car.objects.select_related('owner').all()


class HealthCheckView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response({'status': 'ok', 'message': 'Car rental backend is running'})
