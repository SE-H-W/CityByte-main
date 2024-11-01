from django.contrib import admin
from django.urls import path, include
from search.views import main_page
from info.views import info_page, profile_page, addTofav
from .views import SignUpView
from apps.accounts.views import signup
from apps.accounts.views import signup, CustomLoginView
from . import views
urlpatterns = [
    path("", main_page, name="main_page"),
    path("accounts/signup/", signup, name="signup"),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("profile/", profile_page, name="profile_page"),
    path("city", info_page, name="info_page"),
    path("admin/", admin.site.urls),
    path(
        "api/search/", include(("search.urls", "search"), namespace="search")
    ),
    path("api/info/", include(("info.urls", "info"), namespace="info")),
    path("api/addToFav/", addTofav, name="addToFav"),
    path('city/<str:city_name>/', views.city_info, name='city_info'),
    path('city/<str:city>/<str:country>/news/', views.city_news, name='city_news'),
    # path('city/<str:city>/news/', views.city_news, name='city_news'),
]