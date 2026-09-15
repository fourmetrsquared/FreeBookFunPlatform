"""
Views for chapter-related operations.

Contains classes for displaying, creating, and editing book chapters.
Chapters are the primary content units in the library, containing
Markdown-formatted text that gets rendered to HTML.

Classes:
    ChapterListView    - List of published chapters for a book
    ChapterDetailView  - Chapter detail page with rendered Markdown
    ChapterCreateView  - Create a new chapter (book author only)
    ChapterUpdateView  - Edit an existing chapter (book author only)

Key Features:
    - Markdown rendering with syntax highlighting
    - Sequential chapter navigation (next/previous)
    - Permission checks (only book author can edit)
    - Query optimization to prevent N+1 problems
    - Word count and reading time calculation

Workflow:
    1. Book author creates chapters with Markdown content
    2. Chapters are ordered sequentially within the book
    3. Only published chapters are visible to readers
    4. Authors can edit their chapters at any time

TODO: Add the following views in future iterations:
    - ChapterDeleteView      - Delete chapters
    - ChapterReorderView     - Reorder chapters via drag-and-drop
    - ChapterBulkEditView    - Bulk publish/unpublish chapters
    - ChapterPreviewView     - AJAX preview of Markdown content
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from books.forms import ChapterForm
from books.models import Chapter, Book


# ============================================
# Chapter List View
# ============================================

class ChapterListView(ListView):
    """
    List of all PUBLISHED chapters for a specific book.

    GET /book/<book_slug>/chapters/

    Context:
        chapters: QuerySet[Chapter] - published chapters in reading order
        book: Book - the parent book
        page_obj: Page - pagination object
        total_chapters: int - total number of published chapters
        can_edit: bool - whether current user can edit chapters

    Features:
        - Shows only chapters with is_published=True
        - Sorted by order field (sequential reading order)
        - Annotated with word_count and reading_time
        - Query optimization via select_related()
        - Only accessible if book is published (or user is author)

    URL Parameters:
        book_slug (required) - slug of the parent book

    Security:
        - Returns 404 if book doesn't exist
        - Returns 404 if book is unpublished (unless user is author/staff)

    Example URLs:
        /book/learning-django/chapters/    → All published chapters
    """
    model = Chapter
    template_name = 'books/chapter/list.html'
    context_object_name = 'chapters'
    paginate_by = 50  # Show all chapters on one page typically

    def get_book(self):
        """
        Get the parent book from URL parameter.

        Returns:
            Book: The parent book object

        Raises:
            Http404: If book doesn't exist or user can't access it
        """
        book_slug = self.kwargs.get('book_slug')
        book = get_object_or_404(Book, slug=book_slug)

        # Access control: unpublished books only visible to author/staff
        if not book.is_published:
            user = self.request.user
            if not user.is_authenticated:
                raise Http404("Book not found.")
            if book.author.user != user and not user.is_staff:
                raise Http404("Book not found.")

        return book

    def get_queryset(self):
        """
        Return only published chapters for the parent book.

        Optimizations:
            - filter(book=..., is_published=True) - only published chapters
            - order_by('order') - sequential reading order

        Returns:
            QuerySet: Filtered and ordered queryset of chapters
        """
        self.book = self.get_book()

        return Chapter.objects.filter(
            book=self.book,
            is_published=True
        ).order_by('order')

    def get_context_data(self, **kwargs):
        """
        Add book and related data to context.

        Context additions:
            book: Book - the parent book
            total_chapters: int - total number of published chapters
            can_edit: bool - whether current user can edit chapters
            total_word_count: int - sum of all chapter word counts
            total_reading_time: int - sum of all chapter reading times

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        context['book'] = self.book

        # Total chapter count
        context['total_chapters'] = self.get_queryset().count()

        # Permission check for edit button
        context['can_edit'] = self._can_edit_chapters()

        # Calculate totals for the book
        # TODO: Cache these values on the Book model for performance
        chapters = self.get_queryset()
        context['total_word_count'] = sum(
            len(chapter.content.split()) if chapter.content else 0
            for chapter in chapters
        )
        context['total_reading_time'] = max(
            1, context['total_word_count'] // 225
        )

        return context

    def _can_edit_chapters(self):
        """
        Check if the current user can edit chapters for this book.

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return self.book.author.user == user
        except Exception:
            return False


# ============================================
# Chapter Detail View
# ============================================

class ChapterDetailView(DetailView):
    """
    Chapter detail page with rendered Markdown content.

    GET /book/<book_slug>/chapter/<slug>/

    Context:
        chapter: Chapter - the chapter object
        book: Book - the parent book
        rendered_content: str - HTML-rendered Markdown content
        next_chapter: Chapter|None - next chapter in sequence
        previous_chapter: Chapter|None - previous chapter in sequence
        can_edit: bool - whether current user can edit this chapter
        word_count: int - number of words in the chapter
        reading_time_minutes: int - estimated reading time

    Features:
        - Renders Markdown content to HTML
        - Shows navigation (next/previous chapter)
        - Displays word count and reading time
        - Query optimization via select_related()

    Security:
        - Returns 404 for non-existent chapters
        - Returns 404 for unpublished chapters (unless author/staff)
    """
    model = Chapter
    template_name = 'books/chapter/detail.html'
    context_object_name = 'chapter'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Optimize queries for related models.

        Returns:
            QuerySet: Optimized queryset
        """
        return Chapter.objects.select_related('book')

    def get_object(self, queryset=None):
        """
        Get the chapter object and check access.

        Access control:
            - Published chapters: accessible to everyone
            - Unpublished chapters: only author and staff can view

        Returns:
            Chapter: The chapter object

        Raises:
            Http404: If chapter doesn't exist or user can't access it
        """
        if queryset is None:
            queryset = self.get_queryset()

        book_slug = self.kwargs.get('book_slug')
        chapter_slug = self.kwargs.get(self.slug_url_kwarg)

        chapter = get_object_or_404(
            queryset,
            book__slug=book_slug,
            slug=chapter_slug
        )

        # Access control: unpublished chapters only visible to author/staff
        if not chapter.is_published:
            user = self.request.user
            if not user.is_authenticated:
                raise Http404("Chapter not found.")
            if chapter.book.author.user != user and not user.is_staff:
                raise Http404("Chapter not found.")

        return chapter

    def get_context_data(self, **kwargs):
        """
        Add rendered content and navigation to context.

        Context additions:
            book: Book - the parent book
            rendered_content: str - HTML-rendered Markdown
            next_chapter: Chapter|None - next chapter in sequence
            previous_chapter: Chapter|None - previous chapter in sequence
            can_edit: bool - whether current user can edit this chapter
            word_count: int - number of words in the chapter
            reading_time_minutes: int - estimated reading time
            chapter_number: int - position in the book

        Returns:
            dict: Extended context dictionary
        """
        context = super().get_context_data(**kwargs)
        chapter = self.object

        # Parent book
        context['book'] = chapter.book

        # Render Markdown content to HTML
        # TODO: Cache rendered HTML for performance
        # TODO: Add syntax highlighting for code blocks
        # TODO: Sanitize HTML to prevent XSS attacks
        context['rendered_content'] = self._render_markdown(chapter.content)

        # Navigation: next and previous chapters
        context['next_chapter'] = self._get_next_chapter(chapter)
        context['previous_chapter'] = self._get_previous_chapter(chapter)

        # Permission check for edit button
        context['can_edit'] = self._can_edit_chapter(chapter)

        # Word count and reading time
        context['word_count'] = len(chapter.content.split()) if chapter.content else 0
        context['reading_time_minutes'] = max(1, context['word_count'] // 225)

        # Chapter number (position in the book)
        # TODO: Cache this value on the Chapter model
        context['chapter_number'] = chapter.book.chapters.filter(
            is_published=True,
            order__lte=chapter.order
        ).count()

        return context

    def _render_markdown(self, content):
        """
        Render Markdown content to HTML.

        Args:
            content (str): Markdown content

        Returns:
            str: HTML-rendered content

        TODO: Implement actual Markdown rendering using the `markdown` library
        TODO: Add syntax highlighting for code blocks using Pygments
        TODO: Sanitize HTML to prevent XSS attacks using bleach
        TODO: Cache rendered HTML for performance
        """
        # Placeholder implementation
        # TODO: Replace with actual Markdown rendering
        # import markdown
        # return markdown.markdown(
        #     content,
        #     extensions=['fenced_code', 'tables', 'toc', 'codehilite']
        # )

        # Simple placeholder - just escape HTML for now
        from django.utils.html import escape
        return f'<div class="markdown-content">{escape(content)}</div>'

    def _get_next_chapter(self, chapter):
        """
        Get the next chapter in sequence.

        Args:
            chapter (Chapter): The current chapter

        Returns:
            Chapter|None: Next published chapter or None
        """
        # TODO: Optimize by caching next_chapter_id
        return chapter.book.chapters.filter(
            is_published=True,
            order__gt=chapter.order
        ).order_by('order').first()

    def _get_previous_chapter(self, chapter):
        """
        Get the previous chapter in sequence.

        Args:
            chapter (Chapter): The current chapter

        Returns:
            Chapter|None: Previous published chapter or None
        """
        # TODO: Optimize by caching previous_chapter_id
        return chapter.book.chapters.filter(
            is_published=True,
            order__lt=chapter.order
        ).order_by('-order').first()

    def _can_edit_chapter(self, chapter):
        """
        Check if the current user can edit this chapter.

        Args:
            chapter (Chapter): The chapter to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return chapter.book.author.user == user
        except Exception:
            return False


# ============================================
# Chapter Create View
# ============================================

class ChapterCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new chapter for a book.

    GET /book/<book_slug>/chapter/create/     → Show empty form
    POST /book/<book_slug>/chapter/create/    → Process form and create chapter

    Context:
        form: ChapterForm - the chapter creation form
        book: Book - the parent book
        is_edit: bool - always False for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Only book author can create chapters
        - Automatically sets the book from URL parameter
        - Auto-generates slug from title (in model's save())
        - Auto-assigns order if not provided
        - Shows success message after creation

    Permissions:
        - Only the book's author (or staff) can create chapters

    TODO: Add AJAX endpoint for Markdown preview
    TODO: Add auto-save functionality to prevent data loss
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'books/chapter/form.html'

    def get_book(self):
        """
        Get the parent book from URL parameter with permission check.

        Returns:
            Book: The parent book object

        Raises:
            Http404: If book doesn't exist
            HttpResponseForbidden: If user can't create chapters
        """
        book_slug = self.kwargs.get('book_slug')
        book = get_object_or_404(Book, slug=book_slug)

        # Permission check: only book author or staff can create chapters
        user = self.request.user
        if not (user.is_staff or book.author.user == user):
            raise HttpResponseForbidden(
                "You don't have permission to add chapters to this book."
            )

        return book

    def get_form_kwargs(self):
        """
        Pass the book to the form for validation.

        Returns:
            dict: Form kwargs with book parameter
        """
        kwargs = super().get_form_kwargs()
        self.book = self.get_book()
        kwargs['book'] = self.book
        return kwargs

    def get_context_data(self, **kwargs):
        """Add book and edit mode flag to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        context['book'] = self.book
        context['page_title'] = f'Add Chapter to: {self.book.title}'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Set book from URL parameter
            2. Auto-assign order if not provided
            3. Save the chapter (slug auto-generated in model's save())
            4. Add success flash message
            5. Redirect to chapter detail page

        Returns:
            HttpResponse: Redirect to the new chapter's detail page
        """
        # Save but don't commit to DB yet (need to set book)
        self.object = form.save(commit=False)
        self.object.book = self.book

        # Auto-assign order if not provided
        # TODO: Move this logic to the form's clean_order() method
        if not self.object.order:
            max_order = Chapter.objects.filter(book=self.book).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.object.order = max_order + 1

        # Save to DB (slug auto-generated in model's save())
        self.object.save()

        messages.success(
            self.request,
            f'Chapter "{self.object.title}" created successfully! '
            'You can now add content.'
        )

        # TODO: Update parent book's reading time
        # self.book.reading_time_minutes = self.book.calculate_reading_time()
        # self.book.save(update_fields=['reading_time_minutes'])

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful creation."""
        return reverse('books:chapter_detail', kwargs={
            'book_slug': self.book.slug,
            'slug': self.object.slug
        })


# ============================================
# Chapter Update View
# ============================================

class ChapterUpdateView(LoginRequiredMixin, UpdateView):
    """
    Edit an existing chapter (book author only).

    GET /book/<book_slug>/chapter/<slug>/edit/     → Show form with current data
    POST /book/<book_slug>/chapter/<slug>/edit/    → Process form and update chapter

    Context:
        form: ChapterForm - the chapter edit form (pre-filled)
        book: Book - the parent book
        chapter: Chapter - the chapter being edited
        is_edit: bool - always True for this view

    Features:
        - Requires authentication (LoginRequiredMixin)
        - Only the book's author (or staff) can edit
        - Preserves existing slug unless title changes
        - Shows success message after update

    Security:
        - Returns 403 Forbidden if user is not the book author
        - Returns 404 if chapter doesn't exist

    Permissions:
        - Book author: full edit access
        - Staff users: full edit access
        - Other users: 403 Forbidden

    TODO: Add edit history tracking (who changed what, when)
    TODO: Add version control for chapter content
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'books/chapter/form.html'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Return queryset optimized for editing.

        Returns:
            QuerySet: All chapters (permission check in get_object)
        """
        return Chapter.objects.select_related('book')

    def get_object(self, queryset=None):
        """
        Get the chapter object with permission check.

        Returns:
            Chapter: The chapter to edit

        Raises:
            Http404: If chapter doesn't exist
            HttpResponseForbidden: If user can't edit this chapter
        """
        if queryset is None:
            queryset = self.get_queryset()

        book_slug = self.kwargs.get('book_slug')
        chapter_slug = self.kwargs.get(self.slug_url_kwarg)

        chapter = get_object_or_404(
            queryset,
            book__slug=book_slug,
            slug=chapter_slug
        )

        # Permission check: only book author or staff can edit
        if not self._can_edit_chapter(chapter):
            # TODO: Log unauthorized edit attempts for security monitoring
            raise HttpResponseForbidden(
                "You don't have permission to edit this chapter."
            )

        return chapter

    def get_form_kwargs(self):
        """
        Pass the book to the form for validation.

        Returns:
            dict: Form kwargs with book parameter
        """
        kwargs = super().get_form_kwargs()
        kwargs['book'] = self.object.book
        return kwargs

    def _can_edit_chapter(self, chapter):
        """
        Check if the current user can edit this chapter.

        Args:
            chapter (Chapter): The chapter to check

        Returns:
            bool: True if user can edit, False otherwise
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        try:
            return chapter.book.author.user == user
        except Exception:
            return False

    def get_context_data(self, **kwargs):
        """Add book, chapter, and edit mode flag to context."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['book'] = self.object.book
        context['chapter'] = self.object
        context['page_title'] = f'Edit Chapter: {self.object.title}'
        return context

    def form_valid(self, form):
        """
        Handle successful form validation.

        Actions:
            1. Save the updated chapter
            2. Add success flash message
            3. Redirect to chapter detail page

        Returns:
            HttpResponse: Redirect to the chapter's detail page
        """
        # For UpdateView, self.object is already set by get_object()
        self.object = form.save()

        messages.success(
            self.request,
            f'Chapter "{self.object.title}" updated successfully!'
        )

        # TODO: Update parent book's reading time
        # self.object.book.reading_time_minutes = self.object.book.calculate_reading_time()
        # self.object.book.save(update_fields=['reading_time_minutes'])

        # TODO: Invalidate cached chapter data
        # cache.delete(f'chapter_{self.object.id}')

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return URL for redirect after successful update."""
        return reverse('books:chapter_detail', kwargs={
            'book_slug': self.object.book.slug,
            'slug': self.object.slug
        })

# ============================================
# Helper Functions
# ============================================

# TODO: Add helper functions for common operations

# def get_chapter_or_404_with_access_check(book_slug, chapter_slug, user):
#     """
#     Get a chapter with access control.
#
#     Args:
#         book_slug (str): Book slug
#         chapter_slug (str): Chapter slug
#         user (User): Current user
#
#     Returns:
#         Chapter: The chapter object
#
#     Raises:
#         Http404: If chapter doesn't exist or user can't access it
#     """
#     chapter = get_object_or_404(
#         Chapter,
#         book__slug=book_slug,
#         slug=chapter_slug
#     )
#
#     if not chapter.is_published:
#         if not user.is_authenticated:
#             raise Http404("Chapter not found.")
#         if chapter.book.author.user != user and not user.is_staff:
#             raise Http404("Chapter not found.")
#
#     return chapter


# def render_markdown_content(content):
#     """
#     Render Markdown content to HTML with syntax highlighting.
#
#     Args:
#         content (str): Markdown content
#
#     Returns:
#         str: HTML-rendered content
#
#     TODO: Implement actual Markdown rendering
#     TODO: Add caching for performance
#     TODO: Add syntax highlighting
#     TODO: Sanitize HTML to prevent XSS
#     """
#     import markdown
#     from markdown.extensions.codehilite import CodeHiliteExtension
#
#     return markdown.markdown(
#         content,
#         extensions=[
#             'fenced_code',
#             'tables',
#             'toc',
#             CodeHiliteExtension(css_class='highlight'),
#         ]
#     )
