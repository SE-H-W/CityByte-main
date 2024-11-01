from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import markdown
from django.core.cache import cache
import os
from django.utils import timezone
#import dotenv
from info.models import FavCityEntry, CitySearchRecord, Comment
from django.contrib.messages import get_messages
#from dotenv import load_dotenv
from unittest.mock import patch, MagicMock
from CityByte.views import initialize_gemini_llm
from unittest.mock import patch, MagicMock
from info.models import FavCityEntry, CitySearchRecord, Comment
import pytest
from unittest.mock import patch
from info.models import FavCityEntry, CitySearchRecord, Comment
from django.core.exceptions import ValidationError
from info.models import FavCityEntry, Comment, CitySearchRecord
from django.db import IntegrityError
from django.contrib.auth import get_user_model
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CityByte.settings")
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

    def test_signup_view_post_invalid_username_taken(self):
        # Test if an invalid POST request due to existing username returns errors
        User.objects.create_user(username='testuser', email='testuser@example.com', password='Password123!')
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'newuser@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)  # Should re-render the form

        # Fetch the form from the response context and check for errors
        form = response.context.get('form')
        self.assertIsNotNone(form)  # Ensure the form is in the context
        self.assertFalse(form.is_valid())  # Form should be invalid
        self.assertIn('username', form.errors)  # Check that 'username' has an error
        self.assertEqual(form.errors['username'], ["A user with that username already exists."])


class ItineraryViewTests(TestCase):
    def test_itinerary_view_with_itinerary_content(self):
        # Test when the itinerary exists for the city using a POST request
        response = self.client.post(reverse('city_info', args=['Atlanta']), {
            'days': '3'
        })
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the template used is itinerary.html
        self.assertTemplateUsed(response, 'info/itinerary.html')
        
        # Check that the context contains the correct city name and itinerary content
        self.assertContains(response, 'Itinerary for Atlanta')  # Checks that the city name appears in the template

    
    def test_itinerary_view_css_classes(self):
        # Test that the CSS classes and styles are applied correctly
        response = self.client.post(reverse('city_info', args=['Paris']), {
            'days': '3'
        })
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check specific CSS classes used in the template
        self.assertContains(response, 'container my-5')
        self.assertContains(response, 'section bg-light p-5 rounded shadow-lg')
        self.assertContains(response, 'section-heading text-center font-weight-bold mb-4')
        self.assertContains(response, 'itinerary-content text-dark')

class CityInfoViewTests(TestCase):
    def setUp(self):
        self.url = reverse('city_info', kwargs={'city_name': 'New York'})

    @patch('CityByte.views.initialize_gemini_llm')
    def test_city_info_post_api_key_not_set(self, mock_initialize_llm):
        mock_initialize_llm.side_effect = Exception("Gemini API Key not set. Please configure the key.")
        
        response = self.client.post(self.url, {'days': '2'})
        self.assertEqual(response.status_code, 500)  # Expecting 500 for missing API key

    def test_city_info_post_empty_request(self):
        response = self.client.post(self.url, {})  # No data
        self.assertEqual(response.status_code, 400)  # Expecting 400 for bad request due to missing 'days'

    
    def test_city_info_post_missing_days(self):
        response = self.client.post(self.url, {'days': ''})  # Missing 'days'
        self.assertEqual(response.status_code, 400)  # Expecting 400 for empty 'days' parameter

class CityNewsViewTests(TestCase):
    def setUp(self):
        self.url = reverse('city_news', kwargs={'city': 'Paris', 'country': 'FR'})  # Testing with one-word city

    @patch('info.helpers.newsapi_helper.NewsAPIHelper.get_city_news')
    def test_city_news_with_articles_one_word_city(self, mock_get_city_news):
        # Mock the response of the get_city_news method for a one-word city
        mock_get_city_news.return_value = [
            {
                "title": "Top Attractions in Paris",
                "url": "https://news.example.com/paris-attractions",
                "source": {"name": "Paris News Daily"},
                "publishedAt": "2024-10-31T08:00:00Z",
                "description": "Explore the top attractions in Paris, the City of Light."
            }
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/news.html')
        
        # Verify that the one-word city name and its articles are correctly rendered
        self.assertContains(response, "Top Attractions in Paris")
        self.assertContains(response, "Paris News Daily")
        self.assertContains(response, "Explore the top attractions in Paris, the City of Light.")
        self.assertContains(response, '<a href="https://news.example.com/paris-attractions" target="_blank">Top Attractions in Paris</a>', html=True)

    @patch('info.helpers.newsapi_helper.NewsAPIHelper.get_city_news')
    def test_city_news_no_articles_one_word_city(self, mock_get_city_news):
        # Mock an empty response for a one-word city to simulate no articles available
        mock_get_city_news.return_value = []

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/news.html')
        
        # Check that the "No news available" message is displayed for the one-word city
        self.assertContains(response, "No news available for this location.")

class ProfilePageViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', password='password')
        self.profile_url = reverse('profile_page')

    def test_profile_page_render_authenticated_user(self):
        # Log in the user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/profile.html')
        
        # Verify the username appears in the page
        self.assertContains(response, 'Hi, Testuser')
        self.assertContains(response, 'Your Favourite Cities')
        self.assertContains(response, 'Top 10 Popular Cities')

    def test_profile_page_render_unauthenticated_user(self):
        # Access profile page without login
        response = self.client.get(self.profile_url)
        
        # Should redirect to login page since the user is not authenticated
        self.assertEqual(response.status_code, 302)  # 302 redirect status
        self.assertIn(reverse('login'), response.url)  # Redirect to login page

    def test_profile_page_with_favorite_cities(self):
        # Create favorite cities for the user
        FavCityEntry.objects.create(user=self.user, city="Paris", country="France")
        FavCityEntry.objects.create(user=self.user, city="Tokyo", country="Japan")
        
        
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that favorite cities are displayed
        self.assertContains(response, 'Paris, France')
        self.assertContains(response, 'Tokyo, Japan')
        
    
    def test_profile_page_no_favorite_cities(self):
        # Log in the user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that the empty message for favorite cities is displayed
        self.assertContains(response, "You don't have any favourite cities yet. Start exploring!")

    def test_profile_page_no_popular_cities(self):
        # Log in the user
        self.client.login(username='testuser', password='password')
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that the empty message for popular cities is displayed
        self.assertContains(response, "Looks like no popular cities yet. Keep exploring!")

class SearchPageViewTests(TestCase):
    def setUp(self):
        # Create a test user and log them in
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.search_url = reverse('main_page')
    
    def test_search_page_render(self):
        # Test if the search page renders successfully for an authenticated user
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search.html')

class CityByteAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        
    def test_add_to_fav_city_addition(self):
        response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.assertEqual(response.json(), {'data': 'added'})
        self.assertTrue(FavCityEntry.objects.filter(city='New York', country='USA', user=self.user).exists())

    def test_add_to_fav_city_removal(self):
        FavCityEntry.objects.create(city='New York', country='USA', user=self.user)
        response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.assertEqual(response.json(), {'data': 'removed'})
        self.assertFalse(FavCityEntry.objects.filter(city='New York', country='USA', user=self.user).exists())

    def test_add_to_fav_invalid_city(self):
        response = self.client.get(reverse('addToFav'), {'city': '', 'country': ''})
        self.assertEqual(response.json(), {'data': None})

    @patch('info.helpers.weather.WeatherBitHelper')
    @patch('info.helpers.newsapi_helper.NewsAPIHelper')
    @patch('info.helpers.places.FourSquarePlacesHelper')
    @patch('search.helpers.photo.UnplashCityPhotoHelper')
    @patch('info.helpers.places.FourSquarePlacesHelper')
    def test_info_page_no_weather_data(self, mock_places_1, mock_photo_helper, mock_places_2, mock_newsapi, mock_weather):
        cache.clear()
        with patch('info.helpers.weather.WeatherBitHelper.get_city_weather', side_effect=Exception("API error")):
            response = self.client.get(reverse('info_page'), {'city': 'Atlanta', 'country': 'USA'})
            self.assertEqual(response.status_code, 200)

class CityByteFavoriteCityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        
    def test_add_to_fav_city_addition(self):
        response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.assertEqual(response.json(), {'data': 'added'})
        self.assertTrue(FavCityEntry.objects.filter(city='New York', country='USA', user=self.user).exists())

    def test_add_to_fav_city_removal(self):
        FavCityEntry.objects.create(city='New York', country='USA', user=self.user)
        response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.assertEqual(response.json(), {'data': 'removed'})
        self.assertFalse(FavCityEntry.objects.filter(city='New York', country='USA', user=self.user).exists())

    def test_add_to_fav_invalid_city(self):
        response = self.client.get(reverse('addToFav'), {'city': '', 'country': ''})
        self.assertEqual(response.json(), {'data': None})

class CityInfoViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")
        
        self.city = "Atlanta"
        self.country = "USA"
        self.url = reverse('city_info', kwargs={'city_name': self.city})

    def test_city_info_favorite_toggle(self):
        response = self.client.get(reverse('addToFav'), {'city': self.city, 'country': self.country})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'data': 'added'})
        self.assertTrue(FavCityEntry.objects.filter(city=self.city, country=self.country, user=self.user).exists())

        response = self.client.get(reverse('addToFav'), {'city': self.city, 'country': self.country})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'data': 'removed'})
        self.assertFalse(FavCityEntry.objects.filter(city=self.city, country=self.country, user=self.user).exists())


class CityByteAPITests2(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        
    def test_fav_city_entry_exists_after_adding(self): 
        self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        entry = FavCityEntry.objects.get(city='New York', country='USA', user=self.user)
        self.assertIsNotNone(entry)  # Ensure the entry exists

    def test_fav_city_entry_count(self):
        self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.client.get(reverse('addToFav'), {'city': 'Los Angeles', 'country': 'USA'})
        self.assertEqual(FavCityEntry.objects.filter(user=self.user).count(), 2)  # Should be 2 favorites

    def test_profile_page_no_favorites(self):
        response = self.client.get(reverse('profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You don't have any favourite cities yet. Start exploring!", count=1)  # Assuming a message is shown

    def test_comment_list_order(self):
        Comment.objects.create(city='Atlanta', country='USA', author=self.user, comment='First comment')
        Comment.objects.create(city='Atlanta', country='USA', author=self.user, comment='Second comment')
        response = self.client.get(reverse('info_page'), {'city': 'Atlanta', 'country': 'USA'})
        comments = response.context['comments']
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].comment, 'First comment') 

class CityByteAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_fav_city_entry_exists_after_adding(self):
        self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        entry = FavCityEntry.objects.get(city='New York', country='USA', user=self.user)
        self.assertIsNotNone(entry)  # Ensure the entry exists

    def test_fav_city_entry_count(self):
        self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        self.client.get(reverse('addToFav'), {'city': 'Los Angeles', 'country': 'USA'})
        self.assertEqual(FavCityEntry.objects.filter(user=self.user).count(), 2)  # Should be 2 favorites

    def test_profile_page_no_favorites(self):
        response = self.client.get(reverse('profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You don't have any favourite cities yet. Start exploring!", count=1)  # Assuming a message is shown

    def test_comment_list_order(self):
        Comment.objects.create(city='New York', country='USA', author=self.user, comment='First comment')
        Comment.objects.create(city='New York', country='USA', author=self.user, comment='Second comment')
        response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
        comments = response.context['comments']
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].comment, 'First comment')  # Check if sorted correctly

    @patch('info.helpers.weather.WeatherBitHelper')
    def test_weather_data_cache(self, mock_weather):
        mock_weather().get_city_weather.return_value = {
            "data": [{"sunrise": "06:30", "sunset": "18:30", "ts": 1627845600, "timezone": "America/New_York"}]
        }
        response1 = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
        weather_info1 = response1.context['weather_info']
        self.assertEqual(weather_info1['sunrise'], '06:30')
        
        response2 = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
        weather_info2 = response2.context['weather_info']
        self.assertEqual(weather_info1, weather_info2)  # Check if the cached data is used

class SignUpTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.common_passwords = {"password", "12345678", "qwerty", "abc12345", "letmein"}

    def is_common_password(self, password):
        return password.lower() in self.common_passwords

    def test_signup_password_too_short(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': 'short',
            'password2': 'short'
        })
        self.assertContains(response, "This password is too short. It must contain at least 8 characters.")

    def test_signup_password_numeric_only(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': '12345678',
            'password2': '12345678'
        })
        self.assertContains(response, "This password is entirely numeric.")

    def test_signup_password_same_as_username(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': 'testuser',
            'password2': 'testuser'
        })
        self.assertContains(response, "The password is too similar to the username.")

    def test_signup_password_same_as_email(self):
        response = self.client.post(reverse('signup'), {
            'email': 'testuser@1.com',
            'password1': 'testuser@1.com',
            'password2': 'testuser@1.com'
        })
        self.assertContains(response, "The password is too similar to the email address.")

    def test_signup_password_common(self):
        for common_password in self.common_passwords:
            response = self.client.post(reverse('signup'), {
                'username': 'testuser',
                'password1': common_password,
                'password2': common_password
            })
            self.assertContains(response, "This password is too common")
    
    def test_signup_empty_username(self):
        response = self.client.post(reverse('signup'), {
            'username': '',
            'password1': 'ValidPass123!',
            'password2': 'ValidPass123!'
        })
        self.assertEqual(response.status_code, 200)  # Form should not be submitted
        self.assertContains(response, 'This field is required.')  # Error message check

    def test_signup_empty_password1(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': 'Password123!',
            'password2': ''
        })
        self.assertEqual(response.status_code, 200)  # Form should not be submitted
        self.assertContains(response, 'This field is required.')  # Error message check

    def test_signup_empty_password2(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'password1': '',
            'password2': 'Password123!'
        })
        self.assertEqual(response.status_code, 200)  # Form should not be submitted
        self.assertContains(response, 'This field is required.')  # Error message check
    
    def test_signup_username_too_long(self):
        long_username = 'u' * 151  # 151 characters long
        response = self.client.post(reverse('signup'), {
            'username': long_username,
            'password1': 'ValidPassword123!',
            'password2': 'ValidPassword123!'
        })
        
        # Check that the response is a 200 (form is re-rendered)
        self.assertEqual(response.status_code, 200)
        
        # Check that the user was not created
        self.assertFalse(User.objects.filter(username=long_username).exists())
        
        # Check that the form contains the error for the username field
        form = response.context['form']
        self.assertTrue(form.errors['username'])
        self.assertIn('Ensure this value has at most 150 characters (it has 151).', form.errors['username'])
        
    def test_login_empty_username(self):
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': 'ValidPass123!'
        })
        self.assertEqual(response.status_code, 200)  # Form should not be submitted
        self.assertContains(response, 'This field is required.')  # Error message check

    def test_login_empty_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)  # Form should not be submitted
        self.assertContains(response, 'This field is required.')  # Error message check

    def test_forgot_password_empty_email(self):
        response = self.client.post(reverse('password_reset'), {
            'email': ''  # Empty email
        })
        self.assertEqual(response.status_code, 200)  # Form should not redirect, stays on the same page
        # Check that the appropriate error message or behavior is enforced
        self.assertContains(response, "This field is required.", html=True)  # Assuming the error message is shown

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

       
class CommentModelTests(TestCase):
    def setUp(self):
        # Create a user for testing
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_create_comment(self):
        comment = Comment.objects.create(city='Paris', country='France', comment='Beautiful city!', author=self.user)
        self.assertIsInstance(comment, Comment)
        self.assertEqual(comment.comment, 'Beautiful city!')
    
    def test_create_duplicate_comment(self):
        Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)

        with self.assertRaises(Exception):
            Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)

    def test_comment_str(self):
        comment = Comment.objects.create(city='Paris', country='France', comment='Nice!', author=self.user)
        self.assertEqual(str(comment), f"Paris-France-{self.user.username}")

    def test_unique_constraint_on_comment(self):
        Comment.objects.create(city='Paris', country='France', comment='Great!', author=self.user)
        with self.assertRaises(Exception):
            Comment.objects.create(city='Paris', country='France', comment='Great!', author=self.user)

    def test_comment_created_on(self):
        comment = Comment.objects.create(city='Paris', country='France', comment='Nice!', author=self.user)
        self.assertIsNotNone(comment.created_on)

    def test_multiple_comments_by_different_authors(self):
        User = get_user_model()
        user2 = User.objects.create_user(username='testuser2', password='testpassword2')
        Comment.objects.create(city='Paris', country='France', comment='Great!', author=self.user)
        Comment.objects.create(city='Paris', country='France', comment='Awesome!', author=user2)
        self.assertEqual(Comment.objects.count(), 2)
    
    def test_create_comment_with_long_text(self):
        long_comment = 'A' * 1000  # 1000 characters
        comment = Comment.objects.create(city='Amsterdam', country='Netherlands', comment=long_comment,
                                         author=self.user)
        self.assertEqual(comment.comment, long_comment)

    def test_create_comment_without_author(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(city='Oslo', country='Norway', comment='Nice city!')


class CitySearchRecordTests(TestCase):
    def setUp(self):
        CitySearchRecord.objects.create(city_name='Paris', country_name='France')

    def test_create_city_search_record(self):
        record = CitySearchRecord.objects.create(city_name='Paris', country_name='France')
        self.assertIsInstance(record, CitySearchRecord)
        self.assertEqual(record.city_name, 'Paris')
        self.assertEqual(record.country_name, 'France')

    def test_city_search_record_str(self):
        record = CitySearchRecord.objects.create(city_name='Paris', country_name='France')
        self.assertEqual(str(record), 'Paris-France')

    def test_create_city_search_record_with_empty_city(self):
        with self.assertRaises(ValidationError):
            record = CitySearchRecord(city_name='', country_name='Germany')
            record.full_clean()  # This will validate the instance

    def test_create_city_search_record_with_empty_country(self):
        with self.assertRaises(ValidationError):
            record = CitySearchRecord(city_name='Berlin', country_name='')
            record.full_clean()  # This will validate the instance


class FavCityEntryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_create_fav_city_entry(self):
        fav_city = FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
        self.assertIsInstance(fav_city, FavCityEntry)
        self.assertEqual(fav_city.city, 'Paris')
        self.assertEqual(fav_city.country, 'France')

    def test_fav_city_entry_str(self):
        fav_city = FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
        self.assertEqual(str(fav_city), f"Paris-France-{self.user.username}")

    def test_duplicate_favorite_city(self):
        FavCityEntry.objects.create(user=self.user, city="Paris", country="France")
        with self.assertRaises(Exception):
            FavCityEntry.objects.create(user=self.user, city="Paris", country="France")

    def test_unique_constraint_on_fav_city_entry(self):
        FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
        with self.assertRaises(Exception):
            FavCityEntry.objects.create(user=self.user, city='Paris', country='France')

    def test_fav_city_entry_user(self):
        fav_city = FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
        self.assertEqual(fav_city.user, self.user)

    def test_multiple_favorite_cities_for_one_user(self):
        FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
        FavCityEntry.objects.create(user=self.user, city='New York', country='USA')
        self.assertEqual(FavCityEntry.objects.count(), 2)
    
    def test_retrieve_favorite_cities_for_user(self):
        FavCityEntry.objects.create(city='Paris', country='France', user=self.user)
        FavCityEntry.objects.create(city='Berlin', country='Germany', user=self.user)
        fav_cities = FavCityEntry.objects.filter(user=self.user)
        self.assertEqual(fav_cities.count(), 2)

    def test_delete_favorite_city_entry(self):
        fav_city = FavCityEntry.objects.create(city='Madrid', country='Spain', user=self.user)
        fav_city.delete()
        self.assertFalse(FavCityEntry.objects.filter(id=fav_city.id).exists())

class CRUDDatabaseTests(TestCase):
    def setUp(self):
        # Set up a user and initial objects
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_create_city_search_record(self):
        """Test that a CitySearchRecord can be created and saved to the database."""
        record = CitySearchRecord.objects.create(city_name="Amsterdam", country_name="Netherlands")
        self.assertEqual(CitySearchRecord.objects.count(), 1)
        self.assertEqual(record.city_name, "Amsterdam")

    def test_update_city_search_record(self):
        """Test updating an existing CitySearchRecord."""
        record = CitySearchRecord.objects.create(city_name="Paris", country_name="France")
        record.city_name = "Lyon"
        record.save()
        updated_record = CitySearchRecord.objects.get(id=record.id)
        self.assertEqual(updated_record.city_name, "Lyon")

    def test_delete_city_search_record(self):
        """Test deleting a CitySearchRecord from the database."""
        record = CitySearchRecord.objects.create(city_name="Berlin", country_name="Germany")
        record_id = record.id
        record.delete()
        self.assertFalse(CitySearchRecord.objects.filter(id=record_id).exists())

    def test_create_and_retrieve_comment(self):
        """Test that a Comment can be created and retrieved from the database."""
        comment = Comment.objects.create(
            city="Copenhagen", country="Denmark", comment="Wonderful place!", author=self.user
        )
        retrieved_comment = Comment.objects.get(id=comment.id)
        self.assertEqual(retrieved_comment.comment, "Wonderful place!")
        self.assertEqual(retrieved_comment.author, self.user)

    def test_update_comment(self):
        """Test updating an existing Comment in the database."""
        comment = Comment.objects.create(
            city="Stockholm", country="Sweden", comment="Lovely city!", author=self.user
        )
        comment.comment = "Changed my mind, it's amazing!"
        comment.save()
        updated_comment = Comment.objects.get(id=comment.id)
        self.assertEqual(updated_comment.comment, "Changed my mind, it's amazing!")

    def test_delete_comment(self):
        """Test deleting a Comment from the database."""
        comment = Comment.objects.create(
            city="Dublin", country="Ireland", comment="Nice city!", author=self.user
        )
        comment_id = comment.id
        comment.delete()
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_create_fav_city_entry(self):
        """Test creating and saving a FavCityEntry."""
        fav_city = FavCityEntry.objects.create(city="Kyoto", country="Japan", user=self.user)
        self.assertEqual(FavCityEntry.objects.count(), 1)
        self.assertEqual(fav_city.city, "Kyoto")

    def test_update_fav_city_entry(self):
        """Test updating a FavCityEntry."""
        fav_city = FavCityEntry.objects.create(city="Rome", country="Italy", user=self.user)
        fav_city.city = "Milan"
        fav_city.save()
        updated_fav_city = FavCityEntry.objects.get(id=fav_city.id)
        self.assertEqual(updated_fav_city.city, "Milan")

    def test_delete_fav_city_entry(self):
        """Test deleting a FavCityEntry from the database."""
        fav_city = FavCityEntry.objects.create(city="Seoul", country="South Korea", user=self.user)
        fav_city_id = fav_city.id
        fav_city.delete()
        self.assertFalse(FavCityEntry.objects.filter(id=fav_city_id).exists())

    def test_retrieve_multiple_records(self):
        """Test retrieving multiple records from the database."""
        CitySearchRecord.objects.create(city_name="Tokyo", country_name="Japan")
        CitySearchRecord.objects.create(city_name="Osaka", country_name="Japan")
        records = CitySearchRecord.objects.all()
        self.assertEqual(records.count(), 2)

    def test_retrieve_filtered_records(self):
        """Test filtering records by a specific field value."""
        CitySearchRecord.objects.create(city_name="Los Angeles", country_name="USA")
        CitySearchRecord.objects.create(city_name="San Francisco", country_name="USA")
        usa_records = CitySearchRecord.objects.filter(country_name="USA")
        self.assertEqual(usa_records.count(), 2)

    def test_save_multiple_comments_same_city(self):
        """Test saving multiple comments for the same city by the same user."""
        Comment.objects.create(city="Paris", country="France", comment="Amazing!", author=self.user)
        Comment.objects.create(city="Paris", country="France", comment="So beautiful!", author=self.user)
        self.assertEqual(Comment.objects.filter(city="Paris", country="France", author=self.user).count(), 2)