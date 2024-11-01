from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from info.models import FavCityEntry, CitySearchRecord, Comment
import pytest
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
    @pytest.mark.parametrize("city, country, expected_photo_link", [
        ("New York", "USA", "https://example.com/photo.jpg"),
        # Add more test cases if needed
    ])
    # def test_info_page_with_valid_data(self, city, country, expected_photo_link):
    #     # Mock the return value of the FourSquarePlacesHelper
    #     FourSquarePlacesHelper.get_place_photo = lambda fsq_id: expected_photo_link
        
    #     # Clear the cache before the test
    #     cache.clear()
        
    #     # Make a GET request to the info page with city and country
    #     response = self.client.get(reverse('info_page'), {'city': city, 'country': country})

    #     # Check if the response is successful
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    #     # Ensure that the photo link is present in the response
    #     self.assertContains(response, expected_photo_link)
    # def test_info_page_with_valid_data(self, mock_photo, mock_places, mock_weather, mock_news):
    #     mock_weather().get_city_weather.return_value = {
    #         "data": [{"sunrise": "05:30", "sunset": "18:30", "ts": 1627845600, "timezone": "America/New_York"}]
    #     }
    #     mock_news().get_city_news.return_value = [{'title': 'News Title'}]
    #     #mock_places().get_places.return_value = [{'name': 'Restaurant A'}, {'name': 'Restaurant B'}]
    #     mock_photo().get_city_photo.return_value = "photo_link"

    #     response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     print(response)
    #     self.assertEqual(response.status_code, 200)
    #     #self.assertContains(response, 'Restaurant A')
    #     self.assertContains(response, 'photo_link')

    # @patch('info.helpers.places.FourSquarePlacesHelper')
    # def test_info_page_no_weather_data(self, mock_places):
    #     #mock_places().get_places.return_value = [{'name': 'Restaurant A'}, {'name': 'Restaurant B'}]
    #     cache.clear()
    #     # Simulating no weather data by raising an exception
    #     with patch('info.helpers.weather.WeatherBitHelper.get_city_weather', side_effect=Exception("API error")):
    #         response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #         self.assertEqual(response.status_code, 200)  # Should still render the page
    #         #self.assertContains(response, 'Restaurant A')

    def test_profile_page(self):
        FavCityEntry.objects.create(city='New York', country='USA', user=self.user)
        response = self.client.get(reverse('profile_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New York')

    