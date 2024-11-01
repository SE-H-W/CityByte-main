from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# class SignUpForm(UserCreationForm):
#     email = forms.EmailField(
#         widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))

#     class Meta:
#         model = User
#         fields = ('username', 'email', 'password1', 'password2')
#         widgets = {
#             'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
#             'password1': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
#             'password2': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
#         }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter your username'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email