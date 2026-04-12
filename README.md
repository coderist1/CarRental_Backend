# Car Rental Backend (Django + DRF)

This backend now serves the shared API for the web and mobile apps.

## Setup

```bash
C:/Users/Acer/AppData/Local/Python/bin/python.exe -m pip install -r requirements.txt
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py migrate
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py runserver
```

## API Endpoints

- `GET /api/health/` - health check
- `POST /api/register/` - register user (supports profile fields and role)
- `POST /api/login/` - login and get JWT `access`/`refresh`
- `GET /api/me/` - authenticated user profile
- `PATCH /api/me/` - update authenticated user profile
- `GET /api/cars/` - list cars
- `POST /api/cars/` - create a car (authenticated)
- `GET /api/cars/<id>/` - retrieve car
- `PATCH /api/cars/<id>/` - update car (authenticated)
- `DELETE /api/cars/<id>/` - delete car (authenticated)
- `GET /api/users/` - list users (admin)
- `PATCH /api/users/<id>/` - update user (admin)
- `DELETE /api/users/<id>/` - delete user (admin)

## HTTPie test examples

### POST request examples

```bash
http POST :8000/api/register/ username=student1 email=student1@example.com password=strongpass123 role=renter
http POST :8000/api/login/ username=student1@example.com password=strongpass123
```

Expected:
- Register: `201 Created`
- Login: `200 OK` with JSON tokens

## CORS

`django-cors-headers` is enabled and currently allows all origins for development.

## Admin

Create admin user:

```bash
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py createsuperuser
```

Open `/admin/` and manage the `Car` model.
