from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from info.models import FavCityEntry, Comment

class FavCityEntryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_create_favorite_city(self):
        entry = FavCityEntry.objects.create(user=self.user, city="New York", country="USA")
        self.assertEqual(entry.city, "New York")
        self.assertEqual(entry.country, "USA")

    def test_duplicate_favorite_city(self):
        FavCityEntry.objects.create(user=self.user, city="Paris", country="France")
        with self.assertRaises(Exception):
            FavCityEntry.objects.create(user=self.user, city="Paris", country="France")


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.fav_city = FavCityEntry.objects.create(user=self.user, city='Paris', country='France')

    def test_create_duplicate_comment(self):
        Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)

        with self.assertRaises(Exception):
            Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)

    def test_create_comment(self):
        comment = Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)
        self.assertEqual(comment.comment, 'Great city!')


class MessagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    def test_add_favorite_city_message(self):
        response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'New York added to favorites.')


class ErrorPageTests(TestCase):
    def test_404_error_page(self):
        response = self.client.get('/nonexistent-url/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')