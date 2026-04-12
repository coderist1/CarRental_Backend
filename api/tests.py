from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

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
