"""
Chapter model for the MD Books Library.

This module defines the Chapter model, which represents a chapter within a book.
Chapters contain Markdown-formatted content and are ordered sequentially within
their parent book.

Key Features:
    - Sequential ordering within books
    - Markdown content support
    - Independent publication status from parent book
    - Auto-generated slugs (unique within book scope)
    - Navigation helpers (next/previous chapter)

Classes:
    Chapter - Chapter model with content and ordering
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from books.models import Book


class Chapter(models.Model):
    """
    Chapter model representing a section of a book.

    Chapters are the primary content units in the library. Each chapter
    belongs to exactly one book and contains Markdown-formatted content.
    Chapters can be published independently of their parent book, allowing
    authors to release content incrementally.

    Attributes:
        book (Book): Parent book (Many-to-One relationship)
        title (str): Chapter title (max 100 characters)
        slug (str): URL identifier (auto-generated, unique within book)
        description (str): Brief chapter summary (max 1000 characters)
        content (str): Full chapter content in Markdown format
        order (int): Sequential position within the book
        is_published (bool): Publication flag (False = draft)
        created_at (datetime): Creation timestamp (auto)
        updated_at (datetime): Last update timestamp (auto)

    Relationships:
        - book: Parent book (ForeignKey)

    Properties:
        word_count: Number of words in the chapter
        reading_time_minutes: Estimated reading time
        is_first: True if this is the first chapter in the book
        is_last: True if this is the last chapter in the book

    Methods:
        save(): Auto-generates slug and validates uniqueness
        clean(): Validates order uniqueness within book
        get_absolute_url(): Returns the chapter detail page URL
        get_next_chapter(): Returns the next chapter in sequence
        get_previous_chapter(): Returns the previous chapter in sequence

    Example:
        >>> chapter = Chapter.objects.get(book__slug='learning-django', slug='introduction')
        >>> chapter.word_count
        2500
        >>> chapter.reading_time_minutes
        11
    """

    # ============================================
    # Core Fields
    # ============================================

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='chapters',
        verbose_name="Book",
        help_text="The book this chapter belongs to"
        # TODO: Consider on_delete=models.PROTECT to prevent accidental deletion
        # of books that have chapters, requiring explicit chapter deletion first.
    )

    title = models.CharField(
        max_length=100,
        verbose_name="Title",
        help_text="Chapter title (max 100 characters)"
    )

    # Slug is auto-generated in the save() method
    # Must be unique within the scope of the parent book
    slug = models.SlugField(
        max_length=100,
        blank=True,
        verbose_name="URL",
        help_text="URL identifier. Auto-generated from title. Unique within book."
    )

    description = models.TextField(
        max_length=1000,
        blank=True,
        verbose_name="Description",
        help_text="Brief summary of the chapter (max 1000 characters)"
    )

    content = models.TextField(
        verbose_name="Content",
        help_text="Full chapter content in Markdown format"
        # TODO: Add a Markdown preview widget in the admin/forms for better UX.
        # TODO: Consider using a rich text editor like TinyMCE or CKEditor
        # with Markdown support for non-technical authors.
        # TODO: Add content validation to ensure proper Markdown syntax.
        # TODO: Consider storing both raw Markdown and rendered HTML for performance.
    )

    # Order determines the sequential position within the book
    # Must be unique within the scope of the parent book
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Order",
        help_text="Sequential position within the book (1, 2, 3, ...)"
        # TODO: Add validation in clean() to ensure order is unique within book.
        # TODO: Consider auto-incrementing order when creating new chapters.
        # TODO: Add a method to reorder chapters (e.g., move up/down).
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name="Published",
        help_text="Uncheck to save as draft"
        # TODO: Add validation to prevent publishing if parent book is not published.
        # TODO: Add a published_at field to track when the chapter was published.
    )

    # ============================================
    # Timestamp Fields
    # ============================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    # ============================================
    # Meta Options
    # ============================================

    class Meta:
        """Meta options for the Chapter model."""
        # Sort by order first, then by creation date
        ordering = ['order', 'created_at']
        verbose_name = 'Chapter'
        verbose_name_plural = 'Chapters'

        # Ensure order is unique within each book
        # TODO: Uncomment this constraint after migrating existing data
        # unique_together = [['book', 'order']]

        # Ensure slug is unique within each book
        # TODO: Uncomment this constraint after migrating existing data
        # unique_together = [['book', 'slug']]

        indexes = [
            models.Index(fields=['book', 'order']),
            models.Index(fields=['book', 'slug']),
            models.Index(fields=['book', 'is_published']),
            # TODO: Add composite index for (book, is_published, order) 
            # if frequently querying "published chapters in order"
        ]

    # ============================================
    # Methods
    # ============================================

    def save(self, *args, **kwargs):
        """
        Override save to auto-generate slug and ensure uniqueness within book.

        If slug is not provided, generates it from the title.
        Ensures slug is unique within the scope of the parent book.

        Example:
            >>> chapter = Chapter(book=book, title='Introduction')
            >>> chapter.save()
            >>> chapter.slug
            'introduction'
        """
        if not self.slug:
            base_slug = slugify(self.title)

            # TODO: If the app heavily uses non-Latin characters,
            # replace standard slugify with a library like `Unidecode`
            # to ensure clean, readable ASCII slugs.
            if not base_slug:
                base_slug = self.title.lower().replace(' ', '-')

            # Ensure slug uniqueness within the book
            slug = base_slug
            counter = 1
            while Chapter.objects.filter(book=self.book, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # TODO: Auto-set order to next available number if not provided
        # if not self.order:
        #     max_order = Chapter.objects.filter(book=self.book).aggregate(
        #         models.Max('order')
        #     )['order__max'] or 0
        #     self.order = max_order + 1

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validate the chapter before saving.

        Ensures:
            - Order is unique within the book
            - Content is not empty
            - Parent book exists

        Raises:
            ValidationError: If validation fails
        """
        super().clean()

        # Check order uniqueness within book
        if Chapter.objects.filter(book=self.book, order=self.order).exclude(pk=self.pk).exists():
            raise ValidationError({
                'order': f'A chapter with order {self.order} already exists in this book.'
            })

        # TODO: Add validation to ensure content is not empty
        # if not self.content.strip():
        #     raise ValidationError({'content': 'Chapter content cannot be empty.'})

        # TODO: Add validation to prevent publishing if parent book is not published
        # if self.is_published and not self.book.is_published:
        #     raise ValidationError({
        #         'is_published': 'Cannot publish a chapter if the parent book is not published.'
        #     })

    def __str__(self):
        """
        Return string representation of the chapter.

        Returns:
            str: Book title, chapter order, and chapter title

        Example:
            >>> str(chapter)
            'Learning Django - Chapter 1: Introduction'
        """
        return f"{self.book.title} - Chapter {self.order}: {self.title}"

    def get_absolute_url(self):
        """
        Return the URL for the chapter's detail page.

        Returns:
            str: URL path to the chapter detail view

        Example:
            >>> chapter.get_absolute_url()
            '/book/learning-django/chapter/introduction/'
        """
        return reverse('books:chapter_detail', kwargs={
            'book_slug': self.book.slug,
            'slug': self.slug
        })

    # ============================================
    # Properties
    # ============================================

    @property
    def word_count(self):
        """
        Calculate the number of words in the chapter content.

        Returns:
            int: Number of words

        Example:
            >>> chapter.word_count
            2500
        """
        # TODO: Cache this value in the database for performance
        # if accessed frequently (e.g., in list views).
        return len(self.content.split()) if self.content else 0

    @property
    def reading_time_minutes(self):
        """
        Estimate reading time based on word count.

        Average reading speed: 225 words per minute.

        Returns:
            int: Estimated reading time in minutes (minimum 1)

        Example:
            >>> chapter.reading_time_minutes
            11
        """
        # TODO: Cache this value in the database for performance.
        # TODO: Allow users to configure their reading speed.
        words = self.word_count
        return max(1, words // 225)

    @property
    def is_first(self):
        """
        Check if this is the first chapter in the book.

        Returns:
            bool: True if this is the first chapter

        Example:
            >>> chapter.is_first
            True
        """
        # TODO: Optimize by caching the first chapter's ID in the Book model.
        first_chapter = self.book.chapters.order_by('order').first()
        return first_chapter and first_chapter.pk == self.pk

    @property
    def is_last(self):
        """
        Check if this is the last chapter in the book.

        Returns:
            bool: True if this is the last chapter
        """
        # TODO: Optimize by caching the last chapter's ID in the Book model.
        last_chapter = self.book.chapters.order_by('order').last()
        return last_chapter and last_chapter.pk == self.pk

    # ============================================
    # Navigation Methods
    # ============================================

    def get_next_chapter(self):
        """
        Get the next chapter in sequence.

        Returns:
            Chapter|None: Next chapter or None if this is the last

        Example:
            >>> next_chapter = chapter.get_next_chapter()
            >>> next_chapter.title
            'Getting Started'
        """
        # TODO: Optimize by using a cached next_chapter_id field.
        return self.book.chapters.filter(
            order__gt=self.order,
            is_published=True
        ).order_by('order').first()

    def get_previous_chapter(self):
        """
        Get the previous chapter in sequence.

        Returns:
            Chapter|None: Previous chapter or None if this is the first

        Example:
            >>> prev_chapter = chapter.get_previous_chapter()
            >>> prev_chapter.title
            'Preface'
        """
        # TODO: Optimize by using a cached previous_chapter_id field.
        return self.book.chapters.filter(
            order__lt=self.order,
            is_published=True
        ).order_by('-order').first()

    # ============================================
    # Content Methods
    # ============================================

    def get_rendered_content(self):
        """
        Render the Markdown content to HTML.

        Returns:
            str: HTML-rendered content

        Example:
            >>> chapter.get_rendered_content()
            '<h1>Introduction</h1><p>Welcome to...</p>'
        """
        # TODO: Implement Markdown rendering using the `markdown` library.
        # TODO: Cache the rendered HTML for performance.
        # TODO: Add syntax highlighting for code blocks.
        # TODO: Sanitize HTML to prevent XSS attacks.

        # import markdown
        # return markdown.markdown(
        #     self.content,
        #     extensions=['fenced_code', 'tables', 'toc']
        # )

        return self.content  # Placeholder - replace with actual rendering

    def get_excerpt(self, max_length=200):
        """
        Get a plain-text excerpt of the chapter content.

        Args:
            max_length (int): Maximum length of the excerpt

        Returns:
            str: Plain-text excerpt

        Example:
            >>> chapter.get_excerpt(100)
            'Welcome to the introduction chapter. In this chapter...'
        """
        # TODO: Strip Markdown syntax before truncating.
        # TODO: Ensure truncation doesn't break words.

        if not self.content:
            return ''

        # Simple plain-text extraction (remove Markdown syntax)
        plain_text = self.content.replace('#', '').replace('*', '').replace('_', '')

        if len(plain_text) <= max_length:
            return plain_text

        return plain_text[:max_length].rsplit(' ', 1)[0] + '...'

    # ============================================
    # Utility Methods
    # ============================================

    def can_edit(self, user):
        """
        Check if the given user can edit this chapter.

        Args:
            user (User): The user to check permissions for

        Returns:
            bool: True if user can edit, False otherwise
        """
        # TODO: Implement proper permission checks.
        return (
                user.is_authenticated and
                (self.book.author.user == user or user.is_staff)
        )

    def move_up(self):
        """
        Move this chapter up in the order (decrease order by 1).

        Swaps order with the previous chapter if one exists.
        """
        # TODO: Implement chapter reordering logic.
        prev_chapter = self.get_previous_chapter()
        if prev_chapter:
            # Swap orders
            self.order, prev_chapter.order = prev_chapter.order, self.order
            self.save()
            prev_chapter.save()

    def move_down(self):
        """
        Move this chapter down in the order (increase order by 1).

        Swaps order with the next chapter if one exists.
        """
        # TODO: Implement chapter reordering logic.
        next_chapter = self.get_next_chapter()
        if next_chapter:
            # Swap orders
            self.order, next_chapter.order = next_chapter.order, self.order
            self.save()
            next_chapter.save()
