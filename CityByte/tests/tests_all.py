from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase
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
import pytest
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

    # @patch("info.views.WeatherBitHelper.get_city_weather")
    # @patch("info.views.NewsAPIHelper.get_city_news")
    # @patch("info.helpers.places.FourSquarePlacesHelper.get_places")
    # def test_city_info_page_render(self, mock_get_places, mock_get_city_news, mock_get_city_weather):
    #     # Mock responses for weather, news, and places data
    #     mock_get_city_weather.return_value = {
    #         'city_name': self.city, 
    #         'state_code': 'GA', 
    #         'country_code': 'US', 
    #         'temp': 22, 
    #         'app_temp': 24,
    #         'pres': 1015, 
    #         'wind_spd': 5.5, 
    #         'wind_dir': 180, 
    #         'clouds': 75, 
    #         'precip': 0, 
    #         'uv': 5, 
    #         'sunrise': "06:00", 
    #         'sunset': "18:00"
    #     }
    #     mock_get_city_news.return_value = [
    #         {"title": "News about Atlanta", "url": "http://example.com", "source": {"name": "Example News"}, "publishedAt": timezone.now()}
    #     ]
    #     mock_get_places.return_value = [
    #         {"name": "Central Park", "fsq_id": "1234", "location": {"formatted_address": "Atlanta, GA"}, "categories": [{"name": "Park"}]}
    #     ]
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "info/city_info.html")

    #     # Check for specific elements in the response content
    #     self.assertContains(response, "Temperature")
    #     self.assertContains(response, "22 °C")
    #     self.assertContains(response, "Top Rated Dining Spots")
    #     self.assertContains(response, "Central Park")
    #     self.assertContains(response, "News about Atlanta")
    #     self.assertContains(response, "Comments")

    # @patch("info.helpers.weather.WeatherBitHelper.get_city_weather")
    # def test_city_info_weather_data_display(self, mock_get_city_weather):
    #     mock_get_city_weather.return_value = {
    #         'city_name': self.city, 
    #         'state_code': 'GA', 
    #         'country_code': 'US', 
    #         'temp': 25, 
    #         'app_temp': 26, 
    #         'pres': 1000, 
    #         'wind_spd': 3.5, 
    #         'wind_dir': 90, 
    #         'clouds': 50, 
    #         'precip': 1, 
    #         'uv': 7, 
    #         'sunrise': "06:30", 
    #         'sunset': "19:00"
    #     }
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Temperature")
    #     self.assertContains(response, "25 °C")
    #     self.assertContains(response, "RealFeel Temperature")
    #     self.assertContains(response, "26 °C")

    def test_city_info_favorite_toggle(self):
        response = self.client.get(reverse('addToFav'), {'city': self.city, 'country': self.country})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'data': 'added'})
        self.assertTrue(FavCityEntry.objects.filter(city=self.city, country=self.country, user=self.user).exists())

        response = self.client.get(reverse('addToFav'), {'city': self.city, 'country': self.country})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'data': 'removed'})
        self.assertFalse(FavCityEntry.objects.filter(city=self.city, country=self.country, user=self.user).exists())

    # def test_city_info_comment_post(self):
    #     comment_text = "Great place to visit!"
    #     response = self.client.post(self.url, {'comment': comment_text})
    #     self.assertEqual(response.status_code, 302)

    #     comment = Comment.objects.filter(city=self.city, country=self.country, author=self.user).first()
    #     self.assertIsNotNone(comment)
    #     self.assertEqual(comment.comment, comment_text)

    # @patch("info.helpers.places.FourSquarePlacesHelper.get_places")
    # def test_city_info_dining_spots_display(self, mock_get_places):
    #     mock_get_places.return_value = [
    #         {"name": "Fancy Restaurant", "fsq_id": "5678", "location": {"formatted_address": "Fancy Street, Atlanta, GA"}, "categories": [{"name": "Restaurant"}]}
    #     ]
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Top Rated Dining Spots")
    #     self.assertContains(response, "Fancy Restaurant")

    # @patch("info.helpers.newsapi_helper.NewsAPIHelper.get_city_news")
    # def test_city_info_news_section(self, mock_get_city_news):
    #     mock_get_city_news.return_value = [
    #         {"title": "Latest Events in Atlanta", "url": "https://example.com", "source": {"name": "ATL News"}, "publishedAt": timezone.now()},
    #     ]
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Latest Events in Atlanta")
    #     self.assertContains(response, "ATL News")

    # @patch("info.helpers.places.FourSquarePlacesHelper.get_places")
    # def test_city_info_landmarks_display(self, mock_get_places):
    #     mock_get_places.return_value = [
    #         {"name": "Statue of Liberty", "fsq_id": "4321", "location": {"formatted_address": "Liberty Island, Atlanta, GA"}, "categories": [{"name": "Landmark"}]}
    #     ]
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Top Landmark Spots")
    #     self.assertContains(response, "Statue of Liberty")

    # @patch("info.helpers.places.FourSquarePlacesHelper.get_places")
    # def test_city_info_arts_spots_display(self, mock_get_places):
    #     mock_get_places.return_value = [
    #         {"name": "Museum of Modern Art", "fsq_id": "8765", "location": {"formatted_address": "Museum Mile, Atlanta, GA"}, "categories": [{"name": "Art Museum"}]}
    #     ]
        
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Top Arts Spots")
    #     self.assertContains(response, "Museum of Modern Art")


class CityByteAPITests2(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        
    # def test_info_page_invalid_city(self): 
    #     response = self.client.get(reverse('info_page'), {'city': '', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertContains(response, 'Invalid city or country', count=0)  # Assuming a message is shown
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
    # def test_comment_submission(self):
    #     response = self.client.post(reverse('info_page'), {
    #         'city': 'New York',
    #         'country': 'USA',
    #         'comment': 'Great city!',  # Corrected to 'comment'
    #     })
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue(Comment.objects.filter(city='New York', country='USA', author=self.user, comment='Great city!').exists())  # Ensure comment is saved

    def test_comment_list_order(self):
        Comment.objects.create(city='New York', country='USA', author=self.user, comment='First comment')
        Comment.objects.create(city='New York', country='USA', author=self.user, comment='Second comment')
        response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
        comments = response.context['comments']
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].comment, 'First comment') 
    # def test_weather_data_cache(self, mock_weather):
    #     mock_weather().get_city_weather.return_value = {
    #         "data": [{"sunrise": "06:30", "sunset": "18:30", "ts": 1627845600, "timezone": "America/New_York"}]
    #     }
    #     response1 = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     weather_info1 = response1.context['weather_info']
    #     self.assertEqual(weather_info1['sunrise'], '06:30')
        
    #     response2 = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     weather_info2 = response2.context['weather_info']
    #     self.assertEqual(weather_info1, weather_info2)  # Check if the cached data is used

