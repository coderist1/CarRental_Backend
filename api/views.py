from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Booking, Car, EmailLog, LogReport
from .serializers import (
	CarSerializer,
	EmailOrUsernameTokenObtainPairSerializer,
	BookingSerializer,
	EmailLogSerializer,
	LogReportSerializer,
	PasswordChangeSerializer,
	PasswordResetSerializer,
	UserRegisterSerializer,
	UserSerializer,
	UserUpdateSerializer,
)


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
		EmailLog.objects.create(
			recipient=user.email,
			subject='Welcome to IDRMS',
			body='Your account was created successfully.',
			log_type='registration',
			data={'userId': user.id, 'username': user.username},
		)


class LoginView(TokenObtainPairView):
	serializer_class = EmailOrUsernameTokenObtainPairSerializer


class PasswordChangeView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request):
		serializer = PasswordChangeSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		current_password = serializer.validated_data['current_password']
		new_password = serializer.validated_data['new_password']

		if not request.user.check_password(current_password):
			return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

		request.user.set_password(new_password)
		request.user.save(update_fields=['password'])
		return Response({'detail': 'Password updated successfully.'})


class PasswordResetView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = PasswordResetSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data['email'].strip().lower()
		EmailLog.objects.create(
			recipient=email,
			subject='Password reset request',
			body='A password reset request was submitted.',
			log_type='password',
			data={'email': email},
		)
		return Response({'detail': 'If an account exists, reset instructions will be sent.'})


class MeView(APIView):
	def get(self, request):
		return Response(UserSerializer(request.user).data)

	def patch(self, request):
		serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		return Response(UserSerializer(user).data)


class BookingListCreateView(generics.ListCreateAPIView):
	queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
	serializer_class = BookingSerializer

	def get_permissions(self):
		if self.request.method == 'GET':
			return [permissions.IsAuthenticated()]
		return [permissions.IsAuthenticated()]

	def perform_create(self, serializer):
		serializer.save(renter=self.request.user)


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
	serializer_class = BookingSerializer
	permission_classes = [permissions.IsAuthenticated]


class LogReportListCreateView(generics.ListCreateAPIView):
	queryset = LogReport.objects.select_related('reporter', 'vehicle').all()
	serializer_class = LogReportSerializer
	permission_classes = [permissions.IsAuthenticated]

	def perform_create(self, serializer):
		serializer.save(reporter=self.request.user)


class LogReportDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = LogReport.objects.select_related('reporter', 'vehicle').all()
	serializer_class = LogReportSerializer
	permission_classes = [permissions.IsAuthenticated]


class EmailLogListCreateView(generics.ListCreateAPIView):
	queryset = EmailLog.objects.all()
	serializer_class = EmailLogSerializer
	permission_classes = [permissions.IsAuthenticated]


class EmailLogDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = EmailLog.objects.all()
	serializer_class = EmailLogSerializer
	permission_classes = [permissions.IsAuthenticated]


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
		return Response({'status': 'ok', 'message': 'IDRMS backend is running'})
