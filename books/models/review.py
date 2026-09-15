from django.db import models
from accounts.models import Profile
from books.models import Book



class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews')

    class Rating(models.IntegerChoices):
        ONE = 1, '1 звезда'
        TWO = 2, '2 звезды'
        THREE = 3, '3 звезды'
        FOUR = 4, '4 звезды'
        FIVE = 5, '5 звезд'

    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    comment = models.TextField(max_length=2000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book', 'author')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author} - {self.book.title} ({self.rating} звёзд)"