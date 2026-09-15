from .book import BookListView, BookDetailView, BookEditView
from .category import CategoryListView, CategoryDetailView, CategoryEditView
from .chapter import ChapterListView, ChapterDetailView, ChapterEditView
from .review import ReviewListView, ReviewEditView, ReviewDetailView
from .tag import TagListView, TagEditView, TagDetailView

__all__ = [
    "BookListView",
    "BookDetailView",
    "BookEditView",

    "CategoryListView",
    "CategoryDetailView",
    "CategoryEditView",

    "ChapterListView",
    "ChapterDetailView",
    "ChapterEditView",

    "ReviewListView",
    "ReviewEditView",
    "ReviewDetailView",

    "TagListView",
    "TagEditView",
    "TagDetailView",
]