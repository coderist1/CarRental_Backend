import base64
import binascii
import io
import uuid

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Booking, Car, EmailLog, LogReport, UserProfile


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.startswith('data:') and ';base64,' in data:
                data = data.split(';base64,')[1]
            try:
                decoded_file = base64.b64decode(data)
            except (TypeError, binascii.Error):
                self.fail('invalid_image')

            file_name = str(uuid.uuid4())[:12]
            file_extension = self.get_file_extension(file_name, decoded_file)
            data = ContentFile(decoded_file, name=f"{file_name}.{file_extension}")

        return super().to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        try:
            image = Image.open(io.BytesIO(decoded_file))
            extension = image.format.lower()
        except Exception:
            extension = None
        if extension == 'jpeg':
            extension = 'jpg'
        return extension or 'png'


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    middleName = serializers.SerializerMethodField()
    sex = serializers.SerializerMethodField()
    dateOfBirth = serializers.SerializerMethodField()
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
        profile = getattr(obj, 'profile', None)
        parts = [obj.first_name or '', getattr(profile, 'middle_name', '') or '', obj.last_name or '']
        full_name = ' '.join([part for part in parts if part]).strip()
        return full_name or obj.username

    def get_role(self, obj):
        profile = getattr(obj, 'profile', None)
        return getattr(profile, 'role', 'renter')

    def get_middleName(self, obj):
        profile = getattr(obj, 'profile', None)
        return getattr(profile, 'middle_name', '') or ''

    def get_sex(self, obj):
        profile = getattr(obj, 'profile', None)
        return getattr(profile, 'sex', '') or ''

    def get_dateOfBirth(self, obj):
        profile = getattr(obj, 'profile', None)
        return getattr(profile, 'date_of_birth', None)


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
    image = Base64ImageField(required=False, allow_null=True, use_url=True)
    imageUrl = serializers.SerializerMethodField(read_only=True)
    status = serializers.SerializerMethodField()
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

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
            'image',
            'imageUrl',
            'available',
            'status',
            'created_at',
            'updatedAt',
        )

    def get_owner(self, obj):
        if not obj.owner:
            return ''
        full_name = f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return full_name or obj.owner.username

    def get_imageUrl(self, obj):
        if not obj.image:
            return ''
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def to_representation(self, instance):
        data = super().to_representation(instance)
        image_url = self.get_imageUrl(instance)
        data['image'] = image_url
        data['imageUrl'] = image_url
        return data

    def get_status(self, obj):
        return 'available' if obj.available else 'rented'

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated and 'owner' not in validated_data:
            validated_data['owner'] = request.user
        return super().create(validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BookingSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(required=False)
    createdAt = serializers.DateTimeField(read_only=True)
    updatedAt = serializers.DateTimeField(read_only=True)

    def to_internal_value(self, data):
        return dict(data.items()) if hasattr(data, 'items') else dict(data)

    def _resolve_user(self, raw_value, field_name):
        if raw_value is None:
            return None
        if isinstance(raw_value, User):
            return raw_value
        try:
            return User.objects.filter(pk=int(raw_value)).first()
        except (TypeError, ValueError):
            raise serializers.ValidationError({field_name: 'Must be a valid numeric user id.'})

    def _resolve_car(self, raw_value, field_name):
        if raw_value is None:
            return None
        if isinstance(raw_value, Car):
            return raw_value
        try:
            return Car.objects.filter(pk=int(raw_value)).first()
        except (TypeError, ValueError):
            raise serializers.ValidationError({field_name: 'Must be a valid numeric vehicle id.'})

    def to_representation(self, instance):
        data = instance.data or {}
        return {
            'id': instance.id,
            'renterId': instance.renter_id,
            'ownerId': instance.owner_id,
            'vehicleId': instance.vehicle_id,
            'status': instance.status,
            'rentalId': instance.rental_id,
            'createdAt': instance.created_at,
            'updatedAt': instance.updated_at,
            **data,
        }

    def create(self, validated_data):
        data = dict(validated_data)
        status_value = data.pop('status', 'pending')
        renter_id = data.pop('renter', None) or data.pop('renterId', None)
        owner_id = data.pop('owner', None) or data.pop('ownerId', None)
        vehicle_id = data.pop('vehicle', None) or data.pop('vehicleId', None)
        rental_id = data.pop('rental_id', '')
        renter = None
        if renter_id is not None:
            renter = self._resolve_user(renter_id, 'renterId')
            if renter is None:
                raise serializers.ValidationError({'renterId': f'User with id {renter_id} not found.'})
        else:
            raise serializers.ValidationError({'renterId': 'renterId (or renter) is required.'})

        owner = self._resolve_user(owner_id, 'ownerId')
        vehicle = self._resolve_car(vehicle_id, 'vehicleId')
        return Booking.objects.create(
            renter=renter,
            owner=owner,
            vehicle=vehicle,
            status=status_value,
            rental_id=rental_id,
            data=data,
        )

    def update(self, instance, validated_data):
        data = dict(instance.data or {})
        incoming = dict(validated_data)
        if 'status' in incoming:
            instance.status = incoming.pop('status')
        renter_id = incoming.pop('renter', None) or incoming.pop('renterId', None)
        owner_id = incoming.pop('owner', None) or incoming.pop('ownerId', None)
        vehicle_id = incoming.pop('vehicle', None) or incoming.pop('vehicleId', None)
        if renter_id is not None:
            resolved_renter = self._resolve_user(renter_id, 'renterId')
            if resolved_renter is not None:
                instance.renter = resolved_renter
        if owner_id is not None:
            resolved_owner = self._resolve_user(owner_id, 'ownerId')
            if resolved_owner is not None:
                instance.owner = resolved_owner
        if vehicle_id is not None:
            resolved_vehicle = self._resolve_car(vehicle_id, 'vehicleId')
            if resolved_vehicle is not None:
                instance.vehicle = resolved_vehicle
        if 'rental_id' in incoming:
            instance.rental_id = incoming.pop('rental_id')
        data.update(incoming)
        instance.data = data
        instance.save()
        return instance


class LogReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(required=False)
    createdAt = serializers.DateTimeField(read_only=True)
    updatedAt = serializers.DateTimeField(read_only=True)
    checkout = serializers.JSONField(required=False, allow_null=True)
    comments = serializers.JSONField(required=False)

    def to_internal_value(self, data):
        return dict(data.items()) if hasattr(data, 'items') else dict(data)

    def _resolve_user(self, raw_value, field_name):
        if raw_value is None:
            return None
        if isinstance(raw_value, User):
            return raw_value
        try:
            return User.objects.filter(pk=int(raw_value)).first()
        except (TypeError, ValueError):
            raise serializers.ValidationError({field_name: 'Must be a valid numeric user id.'})

    def _resolve_car(self, raw_value, field_name):
        if raw_value is None:
            return None
        if isinstance(raw_value, Car):
            return raw_value
        try:
            return Car.objects.filter(pk=int(raw_value)).first()
        except (TypeError, ValueError):
            raise serializers.ValidationError({field_name: 'Must be a valid numeric vehicle id.'})

    def to_representation(self, instance):
        data = instance.data or {}
        return {
            'id': instance.id,
            'type': instance.report_type,
            'renterId': instance.reporter_id,
            'vehicleId': instance.vehicle_id,
            'rentalId': instance.rental_id,
            'checkout': instance.checkout,
            'comments': instance.comments or [],
            'createdAt': instance.created_at,
            'updatedAt': instance.updated_at,
            **data,
        }

    def create(self, validated_data):
        data = dict(validated_data)
        report_type = data.pop('type', 'checkin')
        reporter_id = data.pop('reporter', None) or data.pop('renterId', None) or data.pop('reporterId', None)
        vehicle_id = data.pop('vehicle', None) or data.pop('vehicleId', None)
        rental_id = data.pop('rental_id', '')
        checkout = data.pop('checkout', None)
        comments = data.pop('comments', [])
        reporter = None
        if reporter_id is not None:
            reporter = self._resolve_user(reporter_id, 'reporterId')
            if reporter is None:
                raise serializers.ValidationError({'reporterId': f'User with id {reporter_id} not found.'})
        else:
            raise serializers.ValidationError({'reporterId': 'reporterId (or renterId/reporter) is required.'})

        vehicle = self._resolve_car(vehicle_id, 'vehicleId')
        return LogReport.objects.create(
            reporter=reporter,
            vehicle=vehicle,
            rental_id=rental_id,
            report_type=report_type,
            data=data,
            checkout=checkout,
            comments=comments or [],
        )

    def update(self, instance, validated_data):
        data = dict(instance.data or {})
        incoming = dict(validated_data)
        if 'type' in incoming:
            instance.report_type = incoming.pop('type')
        reporter_id = incoming.pop('reporter', None) or incoming.pop('renterId', None) or incoming.pop('reporterId', None)
        vehicle_id = incoming.pop('vehicle', None) or incoming.pop('vehicleId', None)
        if reporter_id is not None:
            resolved_reporter = self._resolve_user(reporter_id, 'reporterId')
            if resolved_reporter is not None:
                instance.reporter = resolved_reporter
        if vehicle_id is not None:
            resolved_vehicle = self._resolve_car(vehicle_id, 'vehicleId')
            if resolved_vehicle is not None:
                instance.vehicle = resolved_vehicle
        if 'rental_id' in incoming:
            instance.rental_id = incoming.pop('rental_id')
        if 'checkout' in incoming:
            instance.checkout = incoming.pop('checkout')
        if 'comments' in incoming:
            instance.comments = incoming.pop('comments')
        data.update(incoming)
        instance.data = data
        instance.save()
        return instance


class EmailLogSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    type = serializers.CharField(required=False)
    sentAt = serializers.DateTimeField(read_only=True)

    def to_internal_value(self, data):
        return dict(data.items()) if hasattr(data, 'items') else dict(data)

    def to_representation(self, instance):
        data = instance.data or {}
        return {
            'id': instance.id,
            'to': instance.recipient,
            'subject': instance.subject,
            'body': instance.body,
            'type': instance.log_type,
            'status': instance.status,
            'sentAt': instance.sent_at,
            **data,
        }

    def create(self, validated_data):
        data = dict(validated_data)
        log_type = data.pop('type', 'notification')
        recipient = data.pop('to', data.pop('recipient', ''))
        subject = data.pop('subject', '')
        body = data.pop('body', '')
        status_value = data.pop('status', 'sent')
        return EmailLog.objects.create(
            recipient=recipient,
            subject=subject,
            body=body,
            log_type=log_type,
            status=status_value,
            data=data,
        )

    def update(self, instance, validated_data):
        data = dict(instance.data or {})
        incoming = dict(validated_data)
        if 'type' in incoming:
            instance.log_type = incoming.pop('type')
        if 'to' in incoming or 'recipient' in incoming:
            instance.recipient = incoming.pop('to', incoming.pop('recipient', instance.recipient))
        if 'subject' in incoming:
            instance.subject = incoming.pop('subject')
        if 'body' in incoming:
            instance.body = incoming.pop('body')
        if 'status' in incoming:
            instance.status = incoming.pop('status')
        data.update(incoming)
        instance.data = data
        instance.save()
        return instance


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Keep the existing request shape while allowing explicit email too.
    username = serializers.CharField(required=False, write_only=True)
    email = serializers.EmailField(required=False, write_only=True)

    def to_internal_value(self, data):
        if isinstance(data, dict) and not data.get('username') and data.get('email'):
            data = data.copy()
            data['username'] = data.get('email')
        return super().to_internal_value(data)

    def validate(self, attrs):
        login_value = (attrs.get('username') or attrs.get('email') or '').strip().lower()
        password = attrs.get('password')

        if not login_value or not password:
            raise serializers.ValidationError({'detail': 'Both username/email and password are required.'})

        username_value = login_value
        if '@' in login_value:
            user = User.objects.filter(email__iexact=login_value).first()
            if user:
                username_value = user.username

        token_attrs = {
            self.username_field: username_value,
            'password': password,
        }
        return super().validate(token_attrs)
