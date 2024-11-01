from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from apps.accounts.forms import SignUpForm
from django.contrib.auth.views import LoginView

# Create your views here.
class CustomLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('main_page')  # Redirect to the main page if already logged in
        return super().get(request, *args,**kwargs)



def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('main_page')