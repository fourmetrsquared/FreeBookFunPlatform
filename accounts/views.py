from django.shortcuts import render
from django.views import View
from .forms import UserForm, ProfileForm
from .models import User, Profile


class ProfileView(View):
    def get(self, request, pk):
        user_object = User.objects.get(pk = pk)
        profile_object = Profile.objects.get(user = user_object)
        user_form = UserForm(instance = user_object)
        profile_form = ProfileForm(instance = profile_object)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile_object,
        }
        return render(request, 'accounts/profile.html', context)

    def post(self, request, pk):
        user_object = User.objects.get(pk=pk)
        profile_object = Profile.objects.get(user=user_object)
        user_form = UserForm(request.POST, instance=user_object)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile_object)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile_object,
        }
        return render(request, 'accounts/profile.html', context)

