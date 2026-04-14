# IDRMS Backend (Django + DRF)

This backend serves the shared API for the IDRMS web and mobile apps.

## Setup

```bash

TO DO FIRST:
1. Create virtual environment: pythom -m venv venv
2. Activate: venv\Scripts\activate
3. Install Dependencies: pip install -r requirements.txt
4. Apply Migrations: python manage.py migrate
5. Run Development Server: python manage.py runserver

```

For web/mobile clients on the same LAN, use:

- `http://192.168.254.107:8000/api` (replace IP when your PC IP changes)
- `http://127.0.0.1:8000/api` for local browser testing on the same PC

## API Endpoints

- `GET /api/health/` - health check
- `POST /api/register/` - register user (supports profile fields and role)
- `POST /api/login/` - login and get JWT `access`/`refresh`
- `POST /api/password/change/` - change authenticated user password
- `POST /api/password/reset/` - request password reset
- `GET /api/me/` - authenticated user profile
- `PATCH /api/me/` - update authenticated user profile
- `GET /api/cars/` - list cars
- `POST /api/cars/` - create a car (authenticated)
- `GET /api/cars/<id>/` - retrieve car
- `PATCH /api/cars/<id>/` - update car (authenticated)
- `DELETE /api/cars/<id>/` - delete car (authenticated)
- `GET /api/bookings/` - list bookings (authenticated)
- `POST /api/bookings/` - create a booking (authenticated)
- `GET /api/log-reports/` - list log reports (authenticated)
- `POST /api/log-reports/` - create a log report (authenticated)
- `GET /api/email-logs/` - list email logs (authenticated)
- `POST /api/email-logs/` - create an email log (authenticated)
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
