from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from CityByte.views import initialize_gemini_llm


class CityInfoViewTests(TestCase):
    def setUp(self):
        self.url = reverse('city_info', kwargs={'city_name': 'New York'})

    @patch('CityByte.views.initialize_gemini_llm')
    def test_city_info_post_valid_input(self, mock_initialize_llm):
        # Mock the LLM response
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = {"text": "Day 1: Visit Central Park\nDay 2: Explore Times Square"}
        mock_initialize_llm.return_value = mock_llm_instance

        response = self.client.post(self.url, {'days': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'info/itinerary.html')
        self.assertContains(response, "Day 1: Visit Central Park")
        self.assertContains(response, "Day 2: Explore Times Square")

    @patch('CityByte.views.initialize_gemini_llm')
    def test_city_info_post_api_key_not_set(self, mock_initialize_llm):
        mock_initialize_llm.side_effect = Exception("Gemini API Key not set. Please configure the key.")
        
        response = self.client.post(self.url, {'days': '2'})
        self.assertEqual(response.status_code, 500)  # or whichever status you expect for this error

    def test_city_info_post_empty_request(self):
        response = self.client.post(self.url, {})  # No data
        self.assertEqual(response.status_code, 400)  # Or appropriate status for bad request

    def test_city_info_post_invalid_city_name(self):
        invalid_url = reverse('city_info', kwargs={'city_name': 'InvalidCity'})
        response = self.client.post(invalid_url, {'days': '2'})
        self.assertEqual(response.status_code, 404)  # or other expected behavior

    def test_city_info_post_missing_days(self):
        response = self.client.post(self.url, {'days': ''})  # Missing days
        self.assertEqual(response.status_code, 400)  # Or appropriate status for bad request

    @patch('CityByte.views.initialize_gemini_llm')
    def test_city_info_post_no_response_text(self, mock_initialize_llm):
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = {}  # No response text
        mock_initialize_llm.return_value = mock_llm_instance
        
        response = self.client.post(self.url, {'days': '2'})
        self.assertEqual(response.status_code, 500)  # Adjust as necessary for your error handling
