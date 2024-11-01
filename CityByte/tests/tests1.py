from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from info.models import FavCityEntry, Comment, CitySearchRecord
from django.db import IntegrityError


# add class meta unique in models

# class FavCityEntryModelTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='password')
#
#     def test_create_favorite_city(self):
#         entry = FavCityEntry.objects.create(user=self.user, city="New York", country="USA")
#         self.assertEqual(entry.city, "New York")
#         self.assertEqual(entry.country, "USA")
#
#     def test_duplicate_favorite_city(self):
#         FavCityEntry.objects.create(user=self.user, city="Paris", country="France")
#         with self.assertRaises(Exception):
#             FavCityEntry.objects.create(user=self.user, city="Paris", country="France")
#
#
# class CommentModelTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='testpassword')
#         self.fav_city = FavCityEntry.objects.create(user=self.user, city='Paris', country='France')
#
#     def test_create_duplicate_comment(self):
#         Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)
#
#         with self.assertRaises(Exception):
#             Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)
#
#     def test_create_comment(self):
#         comment = Comment.objects.create(city='Paris', country='France', comment='Great city!', author=self.user)
#         self.assertEqual(comment.comment, 'Great city!')
#
#
# class MessagesTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username='testuser', password='password')
#         self.client.login(username='testuser', password='password')

#     def test_add_favorite_city_message(self):
#         response = self.client.get(reverse('addToFav'), {'city': 'New York', 'country': 'USA'})
#         messages = list(get_messages(response.wsgi_request))
#         self.assertEqual(str(messages[0]), 'New York added to favorites.')


# class ErrorPageTests(TestCase):

#     def test_404_error_page(self):
#         response = self.client.get('/nonexistent-url/')
#         self.assertEqual(response.status_code, 404)
#         self.assertTemplateUsed(response, '404.html')


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
