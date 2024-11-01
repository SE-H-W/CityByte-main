from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'password'})
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password.')

    def test_login_nonexistent_user(self):
        response = self.client.post(reverse('login'), {'username': 'nonexistent', 'password': 'password'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password.')

    def test_login_redirect_if_already_logged_in(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main_page'))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_logout_authenticated_user(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_redirect_if_already_logged_in(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main_page'))


class PasswordResetViewTests(TestCase):
    def test_password_reset_page(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')

    def test_password_reset_valid_email(self):
        User.objects.create_user(username='testuser', email='testuser@example.com', password='password')
        response = self.client.post(reverse('password_reset'), {'email': 'testuser@example.com'})
        self.assertEqual(response.status_code, 302)

    def test_password_reset_invalid_email(self):
        response = self.client.post(reverse('password_reset'), {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('password_reset_done'))


class PasswordChangeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_password_change_valid(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'password',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_change_invalid_old_password(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your old password was entered incorrectly.')


