from django.shortcuts import render, redirect
from django.views.generic import View
from .forms import UserRegisterForm
from django.contrib import messages


class Register(View):

    def get(self, *args, **kwargs):
        form = UserRegisterForm()
        context = {'form': form}
        return render(self.request, 'registration/register.html', context)

    def post(self, *args, **kwargs):
        form = UserRegisterForm(self.request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(self.request, f'Account created successfully! You can now log in as {username}')
            return redirect('store')
