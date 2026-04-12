from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Car, UserProfile


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', default='renter')
    middleName = serializers.CharField(source='profile.middle_name', allow_blank=True, required=False)
    sex = serializers.CharField(source='profile.sex', allow_blank=True, required=False)
    dateOfBirth = serializers.DateField(source='profile.date_of_birth', allow_null=True, required=False)
    firstName = serializers.CharField(source='first_name', allow_blank=True, required=False)
    lastName = serializers.CharField(source='last_name', allow_blank=True, required=False)
    fullName = serializers.SerializerMethodField()
    active = serializers.BooleanField(source='is_active', required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'firstName',
            'lastName',
            'middleName',
            'fullName',
            'role',
            'sex',
            'dateOfBirth',
            'active',
        )

    def get_fullName(self, obj):
        parts = [obj.first_name or '', getattr(obj.profile, 'middle_name', '') or '', obj.last_name or '']
        full_name = ' '.join([part for part in parts if part]).strip()
        return full_name or obj.username


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    middleName = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False, default='renter')
    sex = serializers.ChoiceField(choices=UserProfile.SEX_CHOICES, required=False, allow_blank=True)
    dateOfBirth = serializers.DateField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'firstName',
            'lastName',
            'middleName',
            'role',
            'sex',
            'dateOfBirth',
        )

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        if not email:
            raise serializers.ValidationError({'email': 'Email is required.'})
        attrs['email'] = email

        if not attrs.get('username'):
            base_username = email.split('@')[0][:120] or 'user'
            candidate = base_username
            suffix = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base_username}{suffix}"
                suffix += 1
            attrs['username'] = candidate

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Email is already registered.'})
        return attrs

    def create(self, validated_data):
        middle_name = validated_data.pop('middleName', '')
        role = validated_data.pop('role', 'renter')
        sex = validated_data.pop('sex', '')
        date_of_birth = validated_data.pop('dateOfBirth', None)

        user = User.objects.create_user(**validated_data)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.middle_name = middle_name
        profile.sex = sex
        profile.date_of_birth = date_of_birth
        profile.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name', required=False, allow_blank=True)
    lastName = serializers.CharField(source='last_name', required=False, allow_blank=True)
    middleName = serializers.CharField(required=False, allow_blank=True)
    sex = serializers.ChoiceField(choices=UserProfile.SEX_CHOICES, required=False, allow_blank=True)
    dateOfBirth = serializers.DateField(required=False, allow_null=True)
    active = serializers.BooleanField(source='is_active', required=False)

    class Meta:
        model = User
        fields = ('firstName', 'lastName', 'middleName', 'sex', 'dateOfBirth', 'active')

    def update(self, instance, validated_data):
        middle_name = validated_data.pop('middleName', None)
        sex = validated_data.pop('sex', None)
        date_of_birth = validated_data.pop('dateOfBirth', None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        profile, _ = UserProfile.objects.get_or_create(user=instance)
        if middle_name is not None:
            profile.middle_name = middle_name
        if sex is not None:
            profile.sex = sex
        if date_of_birth is not None:
            profile.date_of_birth = date_of_birth
        profile.save()
        return instance


class CarSerializer(serializers.ModelSerializer):
    ownerId = serializers.IntegerField(source='owner.id', read_only=True)
    ownerEmail = serializers.EmailField(source='owner.email', read_only=True)
    owner = serializers.SerializerMethodField()
    name = serializers.CharField(source='model', required=False)
    pricePerDay = serializers.DecimalField(source='daily_rate', max_digits=8, decimal_places=2, required=False)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = (
            'id',
            'owner',
            'ownerId',
            'ownerEmail',
            'brand',
            'model',
            'name',
            'year',
            'daily_rate',
            'pricePerDay',
            'available',
            'status',
            'created_at',
        )

    def get_owner(self, obj):
        if not obj.owner:
            return ''
        full_name = f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return full_name or obj.owner.username

    def get_status(self, obj):
        return 'available' if obj.available else 'rented'

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated and 'owner' not in validated_data:
            validated_data['owner'] = request.user
        return super().create(validated_data)
