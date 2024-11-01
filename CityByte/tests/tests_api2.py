from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from info.models import FavCityEntry, CitySearchRecord, Comment

class CityByteAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    # def test_info_page_invalid_city(self):
    #     response = self.client.get(reverse('info_page'), {'city': '', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertContains(response, 'Invalid city or country', count=0)  # Assuming a message is shown

    # def test_info_page_without_comment(self):
    #     response = self.client.post(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertNotContains(response, 'Your comment has been submitted')  # Assuming no comment is added

    # @patch('info.helpers.weather.WeatherBitHelper')
    # def test_info_page_weather_api_failure(self, mock_weather):
    #     mock_weather().get_city_weather.side_effect = Exception("API error")
    #     response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertContains(response, 'Weather information is currently unavailable.')

    # @patch('info.helpers.newsapi_helper.NewsAPIHelper')
    # def test_info_page_news_api_failure(self, mock_news):
    #     mock_news().get_city_news.side_effect = Exception("API error")
    #     response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertContains(response, 'No news available for this location.')

    # @patch('info.helpers.places.FourSquarePlacesHelper')
    # def test_info_page_places_api_failure(self, mock_places):
    #     mock_places().get_places.side_effect = Exception("API error")
    #     response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     self.assertEqual(response.status_code, 200)  # Should render the page
    #     self.assertContains(response, 'Places information is currently unavailable.')

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

    # def test_profile_page_with_multiple_favorites(self):
    #     FavCityEntry.objects.create(city='Atlanta', country='USA', user=self.user)
    #     FavCityEntry.objects.create(city='Los Angeles', country='USA', user=self.user)
    #     response = self.client.get(reverse('profile_page'))
    #     print(response)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'Atlanta', count=1)
    #     self.assertContains(response, 'Los Angeles', count=1)

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
        self.assertEqual(comments[0].comment, 'First comment')  # Check if sorted correctly

    # @patch('info.helpers.newsapi_helper.NewsAPIHelper')
    # def test_news_articles_empty_response(self, mock_news):
    #     mock_news().get_city_news.return_value = []
    #     response = self.client.get(reverse('info_page'), {'city': 'New York', 'country': 'USA'})
    #     print(response)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'No news available for this location.')

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
