from django.db import models
from accounts.models import Profile
from django.utils.text import slugify
from django.urls import reverse



class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(max_length=10000, blank=True)
    image = models.ImageField(upload_to='books/category/', blank=True, null=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='category_requests')

    class Status(models.TextChoices):
        PENDING = 'pending', 'На рассмотрении'
        APPROVED = 'approved', 'Одобрено'
        REJECTED = 'rejected', 'Отклонено'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Статус заявки на категорию"
    )

    reviewed_by = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_categories'
    )

    rejection_reason = models.TextField(max_length=1000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Категория (заявка)'
        verbose_name_plural = 'Категории (заявки)'