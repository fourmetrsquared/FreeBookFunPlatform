from django.views.generic import ListView, DetailView, FormView
from books.models import Book
from books.forms import BookForm

class BookListView(ListView):
    model = Book
    template_name = "books/book/list.html"
    context_object_name = "books"

class BookDetailView(DetailView):
    model = Book
    template_name = "books/book/detail.html"
    context_object_name = "book"

class BookEditView(FormView):
    form_class = BookForm
    template_name = "books/book/form.html"
    success_url = "books/book/done.html"