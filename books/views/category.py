from django.views.generic import ListView, DetailView, FormView
from books.models import Category
from books.forms import CategoryForm

class CategoryListView(ListView):
    model = Category
    template_name = "books/category/list.html"
    context_object_name = "categories"

class CategoryDetailView(DetailView):
    model = Category
    template_name = "books/category/detail.html"
    context_object_name = "category"

class CategoryEditView(FormView):
    form_class = CategoryForm
    template_name = "books/category/form.html"
    success_url = "books/category/done.html"