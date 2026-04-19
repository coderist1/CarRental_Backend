import logging
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Car, EmailLog, LogReport
from .serializers import (
	CarSerializer,
	BookingSerializer,
	EmailLogSerializer,
	LogReportSerializer,
	PasswordChangeSerializer,
	PasswordResetSerializer,
	UserRegisterSerializer,
	UserSerializer,
	UserUpdateSerializer,
)


class LoginView(APIView):
	permission_classes = [permissions.AllowAny]
	authentication_classes = []  # Bypass default auth to avoid CSRF check on login

	def post(self, request):
		email = request.data.get('email', '').strip().lower()
		username = request.data.get('username', '').strip()
		password = request.data.get('password', '')

		if not password or (not email and not username):
			return Response(
				{'detail': 'Provide email or username along with password.'},
				status=status.HTTP_400_BAD_REQUEST,
			)

		user = None
		if email:
			user_obj = User.objects.filter(email__iexact=email).first()
			if user_obj:
				user = authenticate(request, username=user_obj.username, password=password)
		else:
			user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return Response(UserSerializer(user).data)
		return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


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


class PasswordChangeView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = PasswordChangeSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		current_password = serializer.validated_data['current_password']
		new_password = serializer.validated_data['new_password']
		email = serializer.validated_data.get('email', '').strip().lower()
		username = serializer.validated_data.get('username', '').strip()

		user = None
		if email:
			user = User.objects.filter(email__iexact=email).first()
		elif username:
			user = User.objects.filter(username=username).first()
		else:
			return Response(
				{'detail': 'Provide email or username.'},
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
				{'detail': 'Provide userId, email, or username.'},
				status=status.HTTP_400_BAD_REQUEST,
			)
		return Response(UserSerializer(user).data)

	def patch(self, request):
		user = self._resolve_target_user(request)
		if not user:
			return Response(
				{'detail': 'Provide userId, email, or username.'},
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

	def get_queryset(self):
		queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
		status_param = self.request.query_params.get('status')
		if status_param:
			return queryset.filter(status__iexact=status_param.strip())
		return queryset


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Booking.objects.select_related('renter', 'owner', 'vehicle').all()
	serializer_class = BookingSerializer
	permission_classes = [permissions.AllowAny]


class LogReportListCreateView(generics.ListCreateAPIView):
	queryset = LogReport.objects.select_related('reporter', 'vehicle').all()
	serializer_class = LogReportSerializer
	permission_classes = [permissions.AllowAny]


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
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def get_queryset(self):
		queryset = Car.objects.select_related('owner').all()
		status_param = self.request.query_params.get('status')
		owner_id = self.request.query_params.get('ownerId')
		if status_param:
			status_value = status_param.strip().lower()
			if status_value in ['rented', 'reserved']:
				queryset = queryset.filter(available=False)
			elif status_value == 'available':
				queryset = queryset.filter(available=True)
		if owner_id:
			try:
				queryset = queryset.filter(owner_id=int(owner_id))
			except (TypeError, ValueError):
				pass
		return queryset

	def perform_create(self, serializer):
		logger = logging.getLogger(__name__)
		user = getattr(self.request, 'user', None)
		auth = getattr(self.request, 'auth', None)
		try:
			data = dict(self.request.data)
			if 'image' in data and isinstance(data.get('image'), str) and len(data['image']) > 100:
				data['image'] = data['image'][:30] + '...[truncated]'
		except Exception:
			data = str(self.request.data)
		logger.warning('Car create attempt: user=%s authenticated=%s auth=%s data=%s',
					   user, bool(user and getattr(user, 'is_authenticated', False)), auth, data)

		if self.request.user and self.request.user.is_authenticated:
			serializer.save(owner=self.request.user)
			return

		owner_candidate = None
		try:
			owner_candidate = (
				self.request.data.get('owner')
				or self.request.data.get('ownerId')
				or self.request.data.get('owner_id')
				or self.request.data.get('user')
				or self.request.data.get('user_id')
				or self.request.data.get('ownerEmail')
				or self.request.data.get('owner_email')
			)
		except Exception:
			owner_candidate = None

		owner_obj = None
		if owner_candidate:
			try:
				cand = str(owner_candidate).strip()
				if cand.isdigit():
					owner_obj = User.objects.filter(pk=int(cand)).first()
				elif '@' in cand:
					owner_obj = User.objects.filter(email__iexact=cand).first()
				else:
					owner_obj = User.objects.filter(username__iexact=cand).first()
			except Exception:
				owner_obj = None

		if owner_obj:
			serializer.save(owner=owner_obj)
			return

		serializer.save()


class CarDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Car.objects.all()
	serializer_class = CarSerializer
	permission_classes = [permissions.AllowAny]
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def get_queryset(self):
		return Car.objects.select_related('owner').all()


class HealthCheckView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response({'status': 'ok', 'message': 'IDRMS backend is running'})
