from abc import ABC, abstractmethod

from django.conf import settings

from info.utils.weather import WeatherBit, WeatherUtilBase
from search.utils.url import URL


class CityWeatherHelperBase(ABC):
    @abstractmethod
    def get_city_weather(self, city: str, **kwargs):
        pass


class WeatherBitHelper(CityWeatherHelperBase):
    def __init__(self, klass: WeatherUtilBase = None, url: URL = None):
        if url is None:
            klass = WeatherBit
            # Initialize URL with required parameters: protocol, host, and port
            url = URL(
                protocol="https",
                host="api.weatherbit.io",
                port=443,
                params={"key": settings.WEATHER_BIT_CONFIG["api_key"]}
            )

        self._weather_util = klass(url=url)

    def get_city_weather(self, city: str, **kwargs):
        return self._weather_util.get_city_weather(city=city, **kwargs)
