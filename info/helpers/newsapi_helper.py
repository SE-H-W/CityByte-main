# info/helpers/newsapi_helper.py
import requests
from django.conf import settings

class NewsAPIHelper:
    def __init__(self):
        self.base_url = settings.NEWSAPI_CONFIG["base_url"]
        self.api_key = settings.NEWSAPI_CONFIG["api_key"]

    def get_city_news(self, city_name):
        url = f"{self.base_url}/everything"
        params = {
            "q": city_name,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "relevance",
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json().get("articles", [])
        else:
            print(f"Error fetching news: {response.status_code}")
            return []