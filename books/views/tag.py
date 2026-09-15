from django.views.generic import ListView, DetailView, FormView
from books.models import Tag
from books.forms import TagForm

class TagListView(ListView):
    model = TagForm
    template_name = "books/tag/list.html"
    context_object_name = "tags"

class TagDetailView(DetailView):
    model = Tag
    template_name = "books/tag/detail.html"
    context_object_name = "tag"

class TagEditView(FormView):
    form_class = TagForm
    template_name = "books/tag/form.html"
    success_url = "books/tag/done.html"