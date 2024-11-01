from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class SignUpViewTests(TestCase):
    def test_signup_view_get(self):
        # Test if the GET request to the signup page returns a status code 200
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_view_post_valid(self):
        # Test if a valid POST request redirects and creates a new user
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect on successful signup
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertEqual(User.objects.get(username='testuser').email, 'testuser@example.com')

    def test_signup_view_post_invalid_password_mismatch(self):
        # Test if an invalid POST request due to password mismatch re-renders the form with errors
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'Password123!',
            'password2': 'differentpassword',
        })
        self.assertEqual(response.status_code, 200)  # Should re-render the form

        # Fetch the form from the response context and check for errors
        form = response.context.get('form')
        self.assertIsNotNone(form)  # Ensure the form is in the context
        self.assertFalse(form.is_valid())  # Form should be invalid
        self.assertIn('password2', form.errors)  # Check that 'password2' has an error
        print(form.errors)
        self.assertEqual(form.errors['password2'], ['The two password fields didn’t match.'])

    # def test_signup_view_post_invalid_username_taken(self):
    #     # Test if an invalid POST request due to existing username returns errors
    #     User.objects.create_user(username='testuser', email='testuser@example.com', password='Password123!')
    #     response = self.client.post(reverse('signup'), {
    #         'username': 'testuser',
    #         'email': 'newuser@example.com',
    #         'password1': 'Password123!',
    #         'password2': 'Password123!',
    #     })
    #     self.assertEqual(response.status_code, 200)  # Should re-render the form
    #      # Fetch the form from the response context and check for errors
    #     form = response.context.get('form')
    #     self.assertIsNotNone(form)  # Ensure the form is in the context
    #     self.assertFalse(form.is_valid())  # Form should be invalid
    #     self.assertIn('username', form.errors)  # Check that 'username' has an error
    #     self.assertEqual(form.errors['username'], ["A user with that username already exists."])

    def test_signup_view_post_invalid_email_taken(self):
        # Test if an invalid POST request due to existing email returns errors
        User.objects.create_user(username='testuser', email='testuser@example.com', password='Password123!')
        response = self.client.post(reverse('signup'), {
            'username': 'testuser1',
            'email': 'testuser@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)  # Should re-render the form

       
