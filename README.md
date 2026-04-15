# IDRMS Backend (Django + DRF)

This backend serves the shared API for the IDRMS web and mobile apps.

## Setup

```bash
C:/Users/Acer/AppData/Local/Python/bin/python.exe -m pip install -r requirements.txt
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py migrate
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py runserver 0.0.0.0:8000
```

For web/mobile clients on the same LAN, use:

- `http://192.168.254.107:8000/api` (replace IP when your PC IP changes)
- `http://127.0.0.1:8000/api` for local browser testing on the same PC

## API Endpoints

- `GET /api/health/` - health check
- `POST /api/register/` - register user (supports profile fields and role)
- `POST /api/login/` - login and get JWT `access`/`refresh`
- `POST /api/login/refresh/` - get a new access token from refresh token
- `POST /api/login/verify/` - verify a JWT token
- `POST /api/password/change/` - change authenticated user password
- `POST /api/password/reset/` - request password reset
- `GET /api/me/` - user profile (use token or pass `userId`, `email`, or `username`)
- `PATCH /api/me/` - update user profile (use token or pass `userId`, `email`, or `username`)
- `GET /api/cars/` - list cars
- `POST /api/cars/` - create a car
- `GET /api/cars/<id>/` - retrieve car
- `PUT /api/cars/<id>/` - replace car
- `PATCH /api/cars/<id>/` - update car
- `DELETE /api/cars/<id>/` - delete car
- `GET /api/bookings/` - list bookings
- `POST /api/bookings/` - create a booking (`renterId` required if no token)
- `GET /api/bookings/<id>/` - retrieve booking
- `PUT /api/bookings/<id>/` - replace booking
- `PATCH /api/bookings/<id>/` - update booking
- `DELETE /api/bookings/<id>/` - delete booking
- `GET /api/log-reports/` - list log reports
- `POST /api/log-reports/` - create a log report (`reporterId`/`renterId` required if no token)
- `GET /api/log-reports/<id>/` - retrieve log report
- `PUT /api/log-reports/<id>/` - replace log report
- `PATCH /api/log-reports/<id>/` - update log report
- `DELETE /api/log-reports/<id>/` - delete log report
- `GET /api/email-logs/` - list email logs
- `POST /api/email-logs/` - create an email log
- `GET /api/email-logs/<id>/` - retrieve email log
- `PUT /api/email-logs/<id>/` - replace email log
- `PATCH /api/email-logs/<id>/` - update email log
- `DELETE /api/email-logs/<id>/` - delete email log
- `GET /api/users/` - list users
- `GET /api/users/<id>/` - retrieve user
- `PUT /api/users/<id>/` - replace user
- `PATCH /api/users/<id>/` - update user
- `DELETE /api/users/<id>/` - delete user

## HTTPie test examples

### POST request examples

```bash
http POST :8000/api/register/ username=student1 email=student1@example.com password=strongpass123 role=renter
http POST :8000/api/login/ username=student1@example.com password=strongpass123
http POST :8000/api/login/refresh/ refresh="PASTE_REFRESH_TOKEN"
http GET :8000/api/me/ "Authorization: Bearer PASTE_ACCESS_TOKEN"
http GET :8000/api/me/ "Authorization: Token PASTE_ACCESS_TOKEN"
```

Expected:
- Register: `201 Created`
- Login: `200 OK` with JSON tokens

## CORS and Auth

`django-cors-headers` is enabled and currently allows all origins for development.
JWT auth accepts both `Bearer` and `Token` authorization headers so the backend works with the lab examples and standard DRF/JWT clients.

## Admin

Create admin user:

```bash
C:/Users/Acer/AppData/Local/Python/bin/python.exe manage.py createsuperuser
```

Open `/admin/` and manage the `Car` model.
