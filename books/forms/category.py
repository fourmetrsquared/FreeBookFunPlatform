from django import forms
from books.models import Category



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = [
            'author',
            'status',
            'reviewed_by',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название категории'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Описание категории'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
