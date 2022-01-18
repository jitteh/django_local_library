import datetime

from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from catalog.models import Author, BookInstance, Book, Genre, Language

# Create your tests here

class AuthorListViewTest(TestCase):
	@classmethod
	def setUpTestData(cls):
		number_of_authors = 8

		for author_id in range(number_of_authors):
			Author.objects.create(
				first_name=f'Modou {author_id}',
				last_name=f'Surname {author_id}',
			)

	def test_view_url_exists_at_desired_location(self):
		response = self.client.get('/catalog/authors/')
		self.assertEqual(response.status_code, 200)

	def test_view_url_accessible_by_name(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)

	def test_view_uses_correct_template(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/author_list.html')

	def test_pagination_is_five(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)
		self.assertTrue('is_paginated' in response.context)
		self.assertTrue(response.context['is_paginated'] == True)
		self.assertEqual(len(response.context['author_list']), 5)

	def test_list_all_authors(self):
		response = self.client.get(reverse('authors')+'?page=2')
		self.assertEqual(response.status_code, 200)
		self.assertTrue('is_paginated' in response.context)
		self.assertTrue(response.context['is_paginated'] == True)
		self.assertEqual(len(response.context['author_list']), 3)


class LoanedBookInstancesByUserListViewTest(TestCase):
	def setUP(self):
		test_user1 = User.objects.create(username='testuser1', password='1X<ISRUkw+tuK')
		test_user2 = User.objects.create(username='testuser2', password='2HJ1vRV0Z&3iD')

		test_user1.save()
		test_user2.save()

		test_author = Author.objects.create(first_name='John', last_name='Smith')
		test_genre = Genre.objects.create(name='Fantasy')
		test_language = Language.objects.create(name='English')
		test_book = Book.objects.create(
			title='Book Title',
			summary='My book summary',
			isbn='ABCDEFG',
			author=test_author,
			language=test_language,
		)

		genre_objects_for_book = Genre.objects.all()
		test_book.genre.set(genre_objects_for_book)
		test_book.save()

		number_of_book_copies = 30
		for book_copy in range(number_of_book_copies):
			return_date = timezone.localtime() + datetime.timedelta(days=book_copy%5)
			the_borrower = test_user1 if book_copy % 2 else test_user2
			status = 'm'
			BookInstance.objects.create(
				book=test_book,
				imprint='Unlikely Imprint, 2016',
				due_back=return_date,
				borrower=the_borrower,
				status=status,
			)

	def test_redirect_if_not_logged_in(self):
		response = self.client.get(reverse('my-borrowed'))
		self.assertRedirects(response, '/accounts/login/?next=/catalog/mybooks/')

	def test_logged_in_uses_correct_template(self):
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('my-borrowed'))

        # Check our user is logged in
		self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
		self.assertEqual(response.status_code, 200)

        # Check we used correct template
		self.assertTemplateUsed(response, 'catalog/bookinstance_list_borrowed_user.html')

	def test_only_borrowed_books_in_list(self):
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('my-borrowed'))

		self.assertEqual(response.status_code, 200)
		self.assertTrue('bookinstance_list' in response.context)
		self.assertEqual(len(response.context['bookinstance_list']), 0)

		books = BookInstance.objects.all()[:10]

		for book in books:
			book.status = 'o'
			book.save()

		response = self.client.get(reverse('my-borrowed'))
		self.assertEqual(str(response.context['user']), 'testuser1')
		self.assertEqual(response.status_code, 200)

		self.assertTrue('bookinstance_list' in response)

		for bookitem in response.context['bookinstance_list']:
			self.assertEqual(response.context['user'], bookitem.borrower)
			self.assertEqual(bookitem.status_code, 'o')

	def test_pages_ordered_by_due_date(self):
		for book in BookInstance.objects.all():
			book.status='o'
			book.save()

		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('my-borrowed'))

		self.assertEqual(str(response.context['user']), 'testuser1')
		self.assertEqual(response.status_code, 200)

		self.assertEqual(len(response.context['bookinstance_list']), 5)

		last_date = 0
		for book in response.context['bookinstance_list']:
			if last_date == 0:
				last_date = book.due_back
			else:
				self.assertTrue(last_date <= book.due_back)
				last_date = book.due_back

