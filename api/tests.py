from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Booking, EmailLog, LogReport

class ApiEndpointTests(APITestCase):
	def test_register_user(self):
		payload = {
			'username': 'student1',
			'email': 'student1@example.com',
			'password': 'strongpass123',
		}
		response = self.client.post('/api/register/', payload, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(User.objects.filter(username='student1').exists())

	def test_login_user(self):
		User.objects.create_user(
			username='student2',
			email='student2@example.com',
			password='strongpass123',
		)

		response = self.client.post(
			'/api/login/',
			{'username': 'student2', 'password': 'strongpass123'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

	def test_login_user_with_email_in_username_field(self):
		User.objects.create_user(
			username='student3',
			email='student3@example.com',
			password='strongpass123',
		)

		response = self.client.post(
			'/api/login/',
			{'username': 'student3@example.com', 'password': 'strongpass123'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

	def test_login_user_with_email_field(self):
		User.objects.create_user(
			username='student4',
			email='student4@example.com',
			password='strongpass123',
		)

		response = self.client.post(
			'/api/login/',
			{'email': 'student4@example.com', 'password': 'strongpass123'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

	def test_password_change_and_reset(self):
		user = User.objects.create_user(
			username='student5',
			email='student5@example.com',
			password='strongpass123',
		)

		login = self.client.post('/api/login/', {'username': 'student5@example.com', 'password': 'strongpass123'}, format='json')
		token = login.data['access']

		change = self.client.post(
			'/api/password/change/',
			{'current_password': 'strongpass123', 'new_password': 'newstrongpass123'},
			format='json',
			HTTP_AUTHORIZATION=f'Bearer {token}',
		)
		self.assertEqual(change.status_code, status.HTTP_200_OK)

		reset = self.client.post('/api/password/reset/', {'email': 'student5@example.com'}, format='json')
		self.assertEqual(reset.status_code, status.HTTP_200_OK)
		self.assertTrue(EmailLog.objects.filter(recipient='student5@example.com').exists())

		user.refresh_from_db()
		self.assertTrue(user.check_password('newstrongpass123'))

	def test_booking_log_report_and_email_log_endpoints(self):
		user = User.objects.create_user(
			username='student6',
			email='student6@example.com',
			password='strongpass123',
		)
		login = self.client.post('/api/login/', {'username': 'student6@example.com', 'password': 'strongpass123'}, format='json')
		token = login.data['access']

		booking_response = self.client.post(
			'/api/bookings/',
			{
				'vehicleId': 1,
				'vehicleName': 'Toyota Vios',
				'ownerName': 'Owner',
				'renterName': 'Student 6',
				'renterEmail': 'student6@example.com',
				'status': 'pending',
			},
			format='json',
			HTTP_AUTHORIZATION=f'Bearer {token}',
		)
		self.assertEqual(booking_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Booking.objects.count(), 1)

		booking_id = booking_response.data['id']
		booking_patch = self.client.patch(
			f'/api/bookings/{booking_id}/',
			{'status': 'approved'},
			format='json',
			HTTP_AUTHORIZATION=f'Bearer {token}',
		)
		self.assertEqual(booking_patch.status_code, status.HTTP_200_OK)

		report_response = self.client.post(
			'/api/log-reports/',
			{
				'type': 'checkin',
				'vehicleId': 1,
				'vehicleName': 'Toyota Vios',
				'renterName': 'Student 6',
				'issues': [],
				'notes': 'ok',
			},
			format='json',
			HTTP_AUTHORIZATION=f'Bearer {token}',
		)
		self.assertEqual(report_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(LogReport.objects.count(), 1)

		email_response = self.client.post(
			'/api/email-logs/',
			{
				'to': 'student6@example.com',
				'subject': 'Hello',
				'body': 'Welcome',
				'type': 'notification',
			},
			format='json',
			HTTP_AUTHORIZATION=f'Bearer {token}',
		)
		self.assertEqual(email_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(EmailLog.objects.count(), 1)
