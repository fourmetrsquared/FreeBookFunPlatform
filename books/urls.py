from django.urls import path
from books.views import (
    BookListView, BookDetailView, BookEditView,
    CategoryListView, CategoryDetailView, CategoryEditView,
    ChapterListView, ChapterDetailView, ChapterEditView,
    ReviewListView, ReviewDetailView, ReviewEditView,
    TagListView, TagDetailView, TagEditView,
)

app_name = 'books'

urlpatterns = [
    path('', BookListView.as_view(), name='book_list'),
    # Books routs
    path('book/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    # TODO: make and add book create view
    path('book/create/', BookEditView.as_view(), name='book_create'),
    path('book/<int:pk>/edit/', BookEditView.as_view(), name='book_edit'),
    # Category routs
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('category/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    # TODO: make and add category create view
    path('category/create/', CategoryEditView.as_view(), name='category_create'),
    path('category/<int:pk>/edit/', CategoryEditView.as_view(), name='category_edit'),
    # Chapter routs
    path('book/<int:pk>/chapters/', ChapterListView.as_view(), name='chapter_list'),
    path('book/<int:pk>/chapter/<int:pk>/', ChapterDetailView.as_view(), name='chapter_detail'),
    # TODO: make and add chapter create view
    path('book/<int:pk>/chapter/create/', ChapterEditView.as_view(), name='chapter_create'),
    path('book/<int:pk>/chapter/<int:pk>/edit/', ChapterEditView.as_view(), name='chapter_edit'),
    # Reviews routs
    path('reviews/', ReviewListView.as_view(), name='review_list'),
    path('review/<int:pk>/', ReviewDetailView.as_view(), name='review_detail'),
    # TODO: make and add review create view
    path('book/<int:pk>/review/create/', ReviewEditView.as_view(), name='review_create'),
    path('review/<int:pk>/edit/', ReviewEditView.as_view(), name='review_edit'),
    # Tags routs
    path('tags/', TagListView.as_view(), name='tag_list'),
    path('tag/<int:pk>/', TagDetailView.as_view(), name='tag_detail'),
    # TODO: make and add tag create view
    path('tag/create/', TagEditView.as_view(), name='tag_create'),
    path('tag/<int:pk>/edit/', TagEditView.as_view(), name='tag_edit'),
]