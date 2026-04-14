from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	ROLE_CHOICES = (
		('admin', 'Admin'),
		('owner', 'Owner'),
		('renter', 'Renter'),
	)
	SEX_CHOICES = (
		('male', 'Male'),
		('female', 'Female'),
		('prefer_not', 'Prefer not to say'),
	)

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='renter')
	middle_name = models.CharField(max_length=150, blank=True)
	sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)

	def __str__(self):
		return f"{self.user.username} ({self.role})"


class Car(models.Model):
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='cars')
	brand = models.CharField(max_length=100)
	model = models.CharField(max_length=100)
	year = models.PositiveIntegerField()
	daily_rate = models.DecimalField(max_digits=8, decimal_places=2)
	available = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return f"{self.brand} {self.model} ({self.year})"


class Booking(models.Model):
	renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_as_renter')
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings_as_owner')
	vehicle = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
	status = models.CharField(max_length=30, default='pending')
	rental_id = models.CharField(max_length=100, blank=True)
	data = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"Booking {self.id} - {self.status}"


class LogReport(models.Model):
	reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='log_reports')
	vehicle = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_reports')
	rental_id = models.CharField(max_length=100, blank=True)
	report_type = models.CharField(max_length=50, default='checkin')
	data = models.JSONField(default=dict, blank=True)
	checkout = models.JSONField(null=True, blank=True)
	comments = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"LogReport {self.id} - {self.report_type}"


class EmailLog(models.Model):
	recipient = models.EmailField()
	subject = models.CharField(max_length=255)
	body = models.TextField()
	log_type = models.CharField(max_length=50, default='notification')
	status = models.CharField(max_length=20, default='sent')
	data = models.JSONField(default=dict, blank=True)
	sent_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-sent_at']

	def __str__(self):
		return f"{self.log_type}: {self.recipient}"
