from django.views.generic import ListView, DetailView, FormView
from books.models import Chapter
from books.forms import ChapterForm

class ChapterListView(ListView):
    model = Chapter
    template_name = "books/chapter/list.html"
    context_object_name = "chapters"

class ChapterDetailView(DetailView):
    model = Chapter
    template_name = "books/chapter/detail.html"
    context_object_name = "chapter"

class ChapterEditView(FormView):
    form_class = ChapterForm
    template_name = "books/chapter/form.html"
    success_url = "books/chapter/done.html"