from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

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


class LoginRefreshView(TokenRefreshView):
	permission_classes = [permissions.AllowAny]


class LoginVerifyView(TokenVerifyView):
	permission_classes = [permissions.AllowAny]


class PasswordChangeView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = PasswordChangeSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		current_password = serializer.validated_data['current_password']
		new_password = serializer.validated_data['new_password']
		email = serializer.validated_data.get('email', '').strip().lower()
		username = serializer.validated_data.get('username', '').strip()

		user = request.user if request.user.is_authenticated else None
		if not user:
			if email:
				user = User.objects.filter(email__iexact=email).first()
			elif username:
				user = User.objects.filter(username=username).first()
			else:
				return Response(
					{'detail': 'Provide email or username when no token is used.'},
					status=status.HTTP_400_BAD_REQUEST,
				)

		if not user:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

		if not user.check_password(current_password):
			return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

		user.set_password(new_password)
		user.save(update_fields=['password'])
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
	permission_classes = [permissions.AllowAny]

	def _resolve_target_user(self, request):
		if request.user and request.user.is_authenticated:
			return request.user

		user_id = request.query_params.get('userId') or request.data.get('userId') or request.data.get('id')
		email = (request.query_params.get('email') or request.data.get('email') or '').strip().lower()
		username = (request.query_params.get('username') or request.data.get('username') or '').strip()

		if user_id:
			return User.objects.filter(pk=user_id).first()
		if email:
			return User.objects.filter(email__iexact=email).first()
		if username:
			return User.objects.filter(username=username).first()
		return None

	def get(self, request):
		user = self._resolve_target_user(request)
		if not user:
			return Response(
				{'detail': 'Provide userId, email, or username when no token is used.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		return Response(UserSerializer(user).data)

	def patch(self, request):
		user = self._resolve_target_user(request)
		if not user:
			return Response(
				{'detail': 'Provide userId, email, or username when no token is used.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		updated_user = serializer.save()
		return Response(UserSerializer(updated_user).data)


class BookingListCreateView(generics.ListCreateAPIView):
	queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
	serializer_class = BookingSerializer
	permission_classes = [permissions.AllowAny]

	def perform_create(self, serializer):
		if self.request.user and self.request.user.is_authenticated:
			serializer.save(renter=self.request.user)
			return
		serializer.save()


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
	serializer_class = BookingSerializer
	permission_classes = [permissions.AllowAny]


class LogReportListCreateView(generics.ListCreateAPIView):
	queryset = LogReport.objects.select_related('reporter', 'vehicle').all()
	serializer_class = LogReportSerializer
	permission_classes = [permissions.AllowAny]

	def perform_create(self, serializer):
		if self.request.user and self.request.user.is_authenticated:
			serializer.save(reporter=self.request.user)
			return
		serializer.save()


class LogReportDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = LogReport.objects.select_related('reporter', 'vehicle').all()
	serializer_class = LogReportSerializer
	permission_classes = [permissions.AllowAny]


class EmailLogListCreateView(generics.ListCreateAPIView):
	queryset = EmailLog.objects.all()
	serializer_class = EmailLogSerializer
	permission_classes = [permissions.AllowAny]


class EmailLogDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = EmailLog.objects.all()
	serializer_class = EmailLogSerializer
	permission_classes = [permissions.AllowAny]


class UserListView(generics.ListAPIView):
	queryset = User.objects.all().select_related('profile').order_by('-date_joined')
	serializer_class = UserSerializer
	permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = User.objects.all().select_related('profile')
	serializer_class = UserUpdateSerializer
	permission_classes = [permissions.AllowAny]

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		return Response(UserSerializer(self.get_object()).data)


class CarListCreateView(generics.ListCreateAPIView):
	queryset = Car.objects.all()
	serializer_class = CarSerializer
	permission_classes = [permissions.AllowAny]
	authentication_classes = []
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def get_queryset(self):
		return Car.objects.select_related('owner').all()


class CarDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Car.objects.all()
	serializer_class = CarSerializer
	permission_classes = [permissions.AllowAny]
	authentication_classes = []
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def get_queryset(self):
		return Car.objects.select_related('owner').all()


class HealthCheckView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response({'status': 'ok', 'message': 'IDRMS backend is running'})
