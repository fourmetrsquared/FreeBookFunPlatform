from django.views.generic import ListView, DetailView, FormView
from books.models import Review
from books.forms import ReviewForm

class ReviewListView(ListView):
    model = ReviewForm
    template_name = "books/review/list.html"
    context_object_name = "reviews"

class ReviewDetailView(DetailView):
    model = Review
    template_name = "books/review/detail.html"
    context_object_name = "review"

class ReviewEditView(FormView):
    form_class = ReviewForm
    template_name = "books/review/form.html"
    success_url = "books/review/done.html"