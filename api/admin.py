from django.contrib import admin
from .models import Booking, Car, EmailLog, LogReport, UserProfile


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
	list_display = ('id', 'brand', 'model', 'year', 'daily_rate', 'available')
	list_filter = ('available', 'brand')
	search_fields = ('brand', 'model')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'role', 'sex', 'date_of_birth')
	list_filter = ('role', 'sex')
	search_fields = ('user__username', 'user__email')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = ('id', 'renter', 'owner', 'vehicle', 'status', 'created_at')
	list_filter = ('status',)
	search_fields = ('renter__username', 'owner__username', 'vehicle__brand', 'vehicle__model')


@admin.register(LogReport)
class LogReportAdmin(admin.ModelAdmin):
	list_display = ('id', 'reporter', 'vehicle', 'report_type', 'created_at')
	list_filter = ('report_type',)
	search_fields = ('reporter__username', 'vehicle__brand', 'vehicle__model')


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
	list_display = ('id', 'recipient', 'log_type', 'status', 'sent_at')
	list_filter = ('log_type', 'status')
	search_fields = ('recipient', 'subject')
