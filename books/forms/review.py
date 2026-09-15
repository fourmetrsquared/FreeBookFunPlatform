from django import forms
from books.models import Review



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = [
            'book',
            'author',
            'created_at',
            'updated_at',
        ]
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Ваш отзыв о книге'}),
        }