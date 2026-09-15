from django.db import models
from accounts.models import Profile
from books.models import Category
from django.utils.text import slugify



class Book(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(max_length=5000, help_text="Описание книги")

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
        limit_choices_to={'status': 'approved'},
        help_text="Категория книги (необязательно)"
    )

    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='books')
    tags = models.ManyToManyField('Tag', blank=True, related_name='books')

    image = models.ImageField(upload_to='books/book/image/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)

    is_published = models.BooleanField(default=False)
    language = models.CharField(max_length=50, default='Русский')
    reading_time_minutes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']