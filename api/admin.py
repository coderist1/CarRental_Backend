from django.contrib import admin
from .models import Car, UserProfile


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
