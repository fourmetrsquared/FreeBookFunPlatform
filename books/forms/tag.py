from django import forms
from books.models import Tag



class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        exclude = ['slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название тега'}),
        }