import datetime

from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from . models import Book, Author, BookInstance, Genre 
from . forms import RenewBookForm, RenewBookModelForm

# Create your views here.

def index(request):
	num_books = Book.objects.all().count()
	num_instances = BookInstance.objects.all().count()
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()
	num_authors = Author.objects.count()
	num_contains_the = Book.objects.filter(title__icontains='the').count()
	num_visits = request.session.get('num_visits', 0)

	request.session['num_visits'] = num_visits + 1

	context = {
		'num_books': num_books,
		'num_instances': num_instances,
		'num_instances_available': num_instances_available,
		'num_authors': num_books,
		'num_contains_the': num_contains_the,
		'num_visits': num_visits
	}
	return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
	model = Book
	paginate_by = 5


class BookDetailView(generic.DetailView):
	model = Book


class AuthorListView(generic.ListView):
	model = Author
	paginate_by = 5


class AuthorDetailView(generic.DetailView):
	model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 3

	def get_queryset(self):
		return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class OnLoanBooksListView(PermissionRequiredMixin, generic.ListView):
	model = BookInstance
	template_name = 'catalog/bookinstance_list_on_loan.html'
	paginate_by = 3
	permission_required = 'catalog.can_mark_returned'

	def get_queryset(self):
		return BookInstance.objects.filter(status__exact='o')


@login_required
@permission_required('catalog.can_renew', raise_exception=True)
def renew_book_librarian(request, pk):
	book_instance = get_object_or_404(BookInstance, pk=pk)
	if request.method == 'POST':
		form = RenewBookModelForm(request.POST)
		if form.is_valid():
			book_instance.due_back = form.cleaned_data['due_back']
			book_instance.save()
			return HttpResponseRedirect(reverse('all-borrowed'))
	else:
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})
	context = {
		'form': form,
		'book_instance': book_instance
	}
	return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorCreate(CreateView):
	model = Author
	fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
	initial = {'date_of_death': '11/06/2020'}


class AuthorUpdate(UpdateView):
	model = Author
	fields = '__all__'


class AuthorDelete(DeleteView):
	model = Author 
	success_url = reverse_lazy('authors')


class BookCreate(CreateView):
	model = Book
	fields = '__all__'
