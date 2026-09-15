from django import forms
from books.models import Chapter



class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        exclude = [
            'book',
            'slug',
            'is_published',
            'created_at',
            'updated_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название главы'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Краткое описание главы'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor',
                'rows': 20,
                'placeholder': 'Содержимое главы в формате Markdown'
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Порядковый номер'}),
        }