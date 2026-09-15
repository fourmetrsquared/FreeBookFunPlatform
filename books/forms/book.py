from django import forms
from books.models import Book



class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = [
            'author',
            'views',
            'likes',
            'slug',
            'is_published',
            'created_at',
            'updated_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название книги'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Описание книги'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Язык книги'}),
            'reading_time_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Время чтения в минутах'}),
        }