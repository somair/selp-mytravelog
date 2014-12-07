import json

from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from django.http.request import HttpRequest
from django.http.response import Http404
from django.template.loader import render_to_string
from django.test import TestCase

from mytravelog.models.album import Album
from mytravelog.models.city import City
from mytravelog.models.user_profile import UserProfile
from mytravelog.unit_tests import util
from mytravelog.views.album import show_album, convert_string_to_date, create_album
from mytravelog.views.city import show_city, get_autocomplete_suggestions
from mytravelog.views.home import show_home
from mytravelog.views.search import search_for_cities_and_users, get_search_results
from mytravelog.views.user import sign_up, sign_in, sign_out


class HomeTest(TestCase):

    def test_url_resolves_to_correct_view(self):
        found = resolve(util.urls['home'])
        self.assertEqual(found.func, show_home)

    def test_if_show_home_returns_correct_html(self):
        response = self.client.get(util.urls['home'])
        expected_html = render_to_string('mytravelog/home.html', {'csrf_token': self.client.cookies['csrftoken'].value})
        self.assertEqual(response.content, expected_html)

    def test_if_show_home_returns_popular_cities(self):
        # add 2 sample cities and check if they are present in the returned html
        util.add_sample_city(util.city1_sample_data)
        util.add_sample_city(util.city2_sample_data)

        # check if both cities are present in the rendered template
        response = self.client.get(util.urls['home'])
        response_content = response.content.decode()
        self.assertIn(util.city1_sample_data['name'], response_content)
        self.assertIn(util.city2_sample_data['name'], response_content)


class CityTest(TestCase):

    def test_all_city_related_urls_resolves_to_correct_functions(self):
        found = resolve(util.urls['city_base'] + 'Test' + '/')
        self.assertEqual(found.func, show_city)

        found = resolve(util.urls['city_autocomplete'])
        self.assertEqual(found.func, get_autocomplete_suggestions)

    def test_if_show_city_returns_correct_html(self):
        # add simple city so that its name can be passed as an argument to show_city
        util.add_sample_city(util.city1_sample_data)

        sample_city = City.objects.get(name=util.city1_sample_data['name'])
        response = self.client.get(util.urls['city_base'] + sample_city.url_name + '/')
        expected_html = render_to_string('mytravelog/city.html', {'requested_city': sample_city,
                                                                  'csrf_token': self.client.cookies['csrftoken'].value,
                                                                  'requested_city_logs': [],
                                                                  'current_user_albums': []})
        self.assertEqual(response.content.decode(), expected_html)

    def test_saving_ranking_and_retrieving_cities(self):
        util.add_sample_city(util.city1_sample_data)
        util.add_sample_city(util.city2_sample_data)

        city1 = City.objects.get(name=util.city1_sample_data['name'])
        self.assertEqual(city1.name, util.city1_sample_data['name'])
        self.assertEqual(city1.country_name, util.city1_sample_data['country_name'])
        self.assertEqual(city1.tourist_count, util.city1_sample_data['tourist_count'])
        self.assertEqual(city1.tourist_growth, util.city1_sample_data['tourist_growth'])
        self.assertEqual(city1.description, util.city1_sample_data['description'])

        city2 = City.objects.get(name=util.city2_sample_data['name'])
        self.assertEqual(city2.name, util.city2_sample_data['name'])
        self.assertEqual(city2.country_name, util.city2_sample_data['country_name'])
        self.assertEqual(city2.tourist_count, util.city2_sample_data['tourist_count'])
        self.assertEqual(city2.tourist_growth, util.city2_sample_data['tourist_growth'])
        self.assertEqual(city2.description, util.city2_sample_data['description'])

        # city2 gets a lower rank than city1 since its tourist count is greater
        self.assertLess(city2.rank, city1.rank)

    def test_autocomplete_city_name_suggestions(self):
        # non ajax request raises 404 error
        self.assertRaises(Http404, get_autocomplete_suggestions, HttpRequest())

        # no results returned since no cities exist
        response = self.client.get(util.urls['city_autocomplete'],
                                   {'search_term': util.city1_sample_data['name']},
                                   'json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(len(json.loads(response.content)), 0)

        # this time one city should be returned since it exists in the db
        util.add_sample_city(util.city1_sample_data)
        response = self.client.get(util.urls['city_autocomplete'],
                                   {'search_term': util.city1_sample_data['name']},
                                   'json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(util.city1_sample_data['name'], json.loads(response.content)[0]['city'])
        self.assertEqual(util.city1_sample_data['country_name'], json.loads(response.content)[0]['country'])


class SearchTest(TestCase):

    def test_search_url_resolves_to_correct_function(self):
        found = resolve(util.urls['search_base'])
        self.assertEqual(found.func, search_for_cities_and_users)

    def test_search_for_cities_and_users_returns_correct_html(self):
        response = self.client.get(util.urls['search_base'], {'query': 'city'})
        expected_html = render_to_string('mytravelog/search.html',
                                         {'csrf_token': self.client.cookies['csrftoken'].value,
                                          'user_profiles': [], 'cities': [],
                                          'results_count': 0,
                                          'query': 'city',
                                          'can_follow': False})
        self.assertEqual(response.content.decode(), expected_html)
        # print expected_html

    def test_correct_search_results_are_returned(self):
        # no cities or user profiles should be returned since they don't exist in the database yet
        results = get_search_results(util.city1_sample_data['name'])
        self.assertEqual(len(results['cities']), 0)
        self.assertEqual(len(results['user_profiles']), 0)

        # add two sample cities
        util.add_sample_city(util.city1_sample_data)
        util.add_sample_city(util.city2_sample_data)

        # if query = 'city1' then only city1 should be returned
        results = get_search_results(util.city1_sample_data['name'])
        self.assertEqual(len(results['cities']), 1)
        self.assertEqual(results['cities'][0].name, util.city1_sample_data['name'])
        self.assertEqual(len(results['user_profiles']), 0)

        # if query = 'city' then both cities should be returned
        results = get_search_results('city')
        self.assertEqual(len(results['cities']), 2)
        self.assertEqual(len(results['user_profiles']), 0)

        # TODO add user profile tests

    def test_Http404_is_raised_when_no_query_provided(self):
        request = HttpRequest()
        request.GET['query'] = 'city'
        self.assertRaises(Http404, search_for_cities_and_users, HttpRequest())


class UserAuthenticationTest(TestCase):
    def test_urls_resolve_to_current_functions(self):
        # check sign up url
        found = resolve(util.urls['sign_up'])
        self.assertEqual(found.func, sign_up)

        # check sign in url
        found = resolve(util.urls['sign_in'])
        self.assertEqual(found.func, sign_in)

        # check sign out url
        found = resolve(util.urls['sign_out'])
        self.assertEqual(found.func, sign_out)

    def test_views_return_correct_html(self):
        # check sign_up view
        response = self.client.get(util.urls['sign_up'])
        expected_html = render_to_string('mytravelog/sign_up.html', {'csrf_token': self.client.cookies['csrftoken'].value})
        self.assertEqual(response.content, expected_html)

        # check sign_in view
        response = self.client.get(util.urls['sign_in'])
        expected_html = render_to_string('mytravelog/sign_in.html', {'csrf_token': self.client.cookies['csrftoken'].value})
        self.assertEqual(response.content, expected_html)

    def test_sign_out_view_redirects_anonymous_users_to_sign_in(self):
        response = self.client.get(util.urls['sign_out'], None, follow=True)
        self.assertRedirects(response, util.urls['sign_in'], status_code=302, target_status_code=200)

    def test_sign_in_and_sign_up_views_redirect_authenticated_users_to_their_profiles(self):
        # create and sign in a new user
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

        # auth user gets redirected to user profile page if they try to sign in or sign up
        response = self.client.post(util.urls['sign_in'], util.user1_sample_data, follow=True)
        self.assertRedirects(response, util.urls['user_base'] + util.user1_sample_data['username'] + '/', status_code=302, target_status_code=200)
        self.client.post(util.urls['sign_up'], util.user1_sample_data, follow=True)
        self.assertRedirects(response, util.urls['user_base'] + util.user1_sample_data['username'] + '/', status_code=302, target_status_code=200)

    def test_sign_up_creates_new_user_and_user_profile(self):
        # on success, a new user and user profile should be created and the user should get redirected to user page
        response = self.client.post(util.urls['sign_up'], util.user1_sample_data, follow=True)
        self.assertRedirects(response, util.urls['user_base'] + util.user1_sample_data['username'] + '/', status_code=302, target_status_code=200)
        new_user = User.objects.get(username=util.user1_sample_data['username'])
        new_user_profile = UserProfile.objects.get(user=new_user)

        # check if all saved data are correct
        self.assertEqual(new_user.username, util.user1_sample_data['username'])
        self.assertEqual(new_user.first_name, util.user1_sample_data['first_name'])
        self.assertEqual(new_user.last_name, util.user1_sample_data['last_name'])
        self.assertEqual(new_user_profile.city_count, 0)
        self.assertEqual(new_user_profile.country_count, 0)
        self.assertEqual(new_user_profile.rank, -1)

    def test_sign_in_view_logs_in_registered_user(self):
        # a user that has never registered before gets an error saying 'Incorrect username or password'
        response = self.client.post(util.urls['sign_in'], util.user1_sample_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Incorrect username or password')

        # an already registered user should get signed in and be redirected to user page
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        response = self.client.post(util.urls['sign_in'], util.user1_sample_data, follow=True)
        self.assertRedirects(response, util.urls['user_base'] + util.user1_sample_data['username'] + '/', status_code=302, target_status_code=200)

    def test_sign_out_view_signs_out_an_authenticated_user(self):
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

    def test_sign_up_validation(self):
        # test all possible validation errors (including uploaded file size errors)
        user_data_dict = {}
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'First name is required')

        user_data_dict['first_name'] = util.user1_sample_data['first_name']
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Last name is required')

        user_data_dict['last_name'] = util.user1_sample_data['last_name']
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Email is required')

        user_data_dict['email'] = 'email'
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Email is missing the \'@\' symbol')

        user_data_dict['email'] = util.user1_sample_data['email']
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Username is required')

        user_data_dict['username'] = 'user'
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Username must be at least 6 characters long')

        user_data_dict['username'] = 'user user'
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Username cannot contain spaces')

        user_data_dict['username'] = util.user1_sample_data['username']
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Password is required')

        user_data_dict['password'] = 'pass'
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Password must be at least 6 characters long')

        user_data_dict['password'] = util.user1_sample_data['password']
        user_data_dict['profile_picture'] = util.get_large_image()
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Max image size allowed is 2 mb')

        user_data_dict['profile_picture'] = util.get_small_image()
        user_data_dict['cover_picture'] = util.get_large_image()
        response = self.client.post(util.urls['sign_up'], user_data_dict)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Max image size allowed is 2 mb')

        user_data_dict['cover_picture'] = util.get_small_image()
        response = self.client.post(util.urls['sign_up'], user_data_dict, follow=True)

        # now that all data is validated, user should be successfully signed up and redirected to user page
        self.assertRedirects(response,
                             util.urls['user_base'] + util.user1_sample_data['username'] + '/',
                             status_code=302,
                             target_status_code=200)

        # sign out and try to create a new user with the same username
        self.client.logout()
        response = self.client.post(util.urls['sign_up'], {'first_name': util.user1_sample_data['first_name'],
                                                           'last_name': util.user1_sample_data['last_name'],
                                                           'email': util.user1_sample_data['email'],
                                                           'username': util.user1_sample_data['username'],
                                                           'password': util.user1_sample_data['password'],
                                                           'profile_picture': util.get_small_image(),
                                                           'cover_picture': util.get_small_image()}, follow=True)
        self.assertEqual(response.context['error'], 'That username is not available')


class AlbumTest(TestCase):

    def test_album_page_url_resolves_to_correct_function(self):
        found = resolve(util.urls['album_show_base'] + '0/')
        self.assertEqual(found.func, show_album)

    def test_show_album_view_returns_correct_html(self):
        # add a new album since show_album view needs an id
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        util.add_sample_album(util.album1_sample_data, util.user1_sample_data)
        album = util.get_album(util.album1_sample_data, util.user1_sample_data)
        user_dict = util.get_user_and_user_profile(util.user1_sample_data)
        user = user_dict['user']
        user_profile = user_dict['user_profile']

        response = self.client.get(util.urls['album_show_base'] + str(album.id) + '/')
        expected_html = render_to_string('mytravelog/user_album.html',
                                         {'csrf_token': self.client.cookies['csrftoken'].value,
                                          'requested_album': album,
                                          'requested_user_albums': [album],
                                          'requested_album_logs': [],
                                          'requested_user': user,
                                          'requested_user_profile': user_profile,
                                          'can_follow': False,
                                          'can_edit_profile': False})

        self.assertEqual(response.content.decode(), expected_html)

    def test_create_album_view(self):
        # non ajax request raises 404 error
        self.assertRaises(Http404, create_album, HttpRequest())
        # anon user gets redirected to sign in page
        response = self.client.post(util.urls['album_create'],
                                    data=util.album1_sample_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['redirect_to'], util.urls['sign_in'])

        # create and sign in a new user
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

        # as the user is now authenticated, album should be created successfully
        self.client.post(util.urls['album_create'],
                         data=util.album1_sample_data,
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # check if all saved data are correct
        album = util.get_album(util.album1_sample_data, util.user1_sample_data)
        self.assertEqual(album.name, util.album1_sample_data['name'])
        self.assertEqual(album.start_date, convert_string_to_date(util.album1_sample_data['start_date']))
        self.assertEqual(album.end_date, convert_string_to_date(util.album1_sample_data['end_date']))

    def test_update_album_view(self):
        # create and retrieve an album to be edited
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        util.add_sample_album(util.album1_sample_data, util.user1_sample_data)
        album = util.get_album(util.album1_sample_data, util.user1_sample_data)

        # non ajax request raises 404 error
        response = self.client.post(util.urls['album_update_base'] + str(album.id) + '/',
                                    data=util.album2_sample_data)
        self.assertEqual(response.status_code, 404)

        # anon user gets redirected to sign in page
        response = self.client.post(util.urls['album_update_base'] + str(album.id) + '/',
                                    data=util.album2_sample_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['redirect_to'], util.urls['sign_in'])

        # sign in user
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

        # as the user is now authenticated, album should be updated successfully
        self.client.post(util.urls['album_update_base'] + str(album.id) + '/',
                         data=util.album2_sample_data,
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # check if all saved data are correct
        album = util.get_album(util.album2_sample_data, util.user1_sample_data)
        self.assertEqual(album.name, util.album2_sample_data['name'])
        self.assertEqual(album.start_date, convert_string_to_date(util.album2_sample_data['start_date']))
        self.assertEqual(album.end_date, convert_string_to_date(util.album2_sample_data['end_date']))

    def test_delete_album_view(self):
        # create and retrieve an album to be delete
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        util.add_sample_album(util.album1_sample_data, util.user1_sample_data)
        album = util.get_album(util.album1_sample_data, util.user1_sample_data)

        # non ajax request raises 404 error
        response = self.client.post(util.urls['album_delete_base'] + str(album.id) + '/',
                                    data=util.album1_sample_data)
        self.assertEqual(response.status_code, 404)

        # anon user gets redirected to sign in page
        response = self.client.post(util.urls['album_delete_base'] + str(album.id) + '/',
                                    data=util.album1_sample_data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['redirect_to'], util.urls['sign_in'])

        # sign in user
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

        # as the user is now authenticated, album should be deleted successfully
        self.client.post(util.urls['album_update_base'] + str(album.id) + '/',
                         data=util.album2_sample_data,
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # check if album was actually deleted
        self.assertEqual(len(Album.objects.filter(name=util.album1_sample_data['name'],
                                                  user_profile__user__username=util.user1_sample_data['username'])), 0)

    def test_album_form_validation(self):
        # create and sign in a new user
        util.add_sample_user_and_user_profile(util.user1_sample_data)
        is_successful = self.client.login(username=util.user1_sample_data['username'],
                                          password=util.user1_sample_data['password'])
        self.assertTrue(is_successful)

        # as the user is now authenticated, we can start our validation checks with an empty dict passed to create_album
        album_data_dict = {

        }
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "Album name is required")

        album_data_dict['name'] = 'None'
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "Album name cannot be 'None'")

        album_data_dict['name'] = util.album1_sample_data['name']
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "Start date is required")

        album_data_dict['start_date'] = util.album1_sample_data['start_date']
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "End date is required")

        album_data_dict['end_date'] = '1900-1-1'
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "End date must come after Start date")

        album_data_dict['end_date'] = util.album1_sample_data['end_date']
        cover_picture = util.get_large_image()
        album_data_dict['cover_picture'] = cover_picture
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "Max image size allowed is 2 mb")

        cover_picture = util.get_small_image()
        album_data_dict['cover_picture'] = cover_picture
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(len(json.loads(response.content)), 0)

        # now try to create another album with the same name
        album_data_dict['cover_picture'] = cover_picture
        response = self.client.post(util.urls['album_create'],
                                    data=album_data_dict,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(json.loads(response.content)['error'], "You already have an album with the same name")

