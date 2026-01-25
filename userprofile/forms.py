from django import forms
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Passwort", 
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-3 py-2 input input-primary"
        })
    )
    password2 = forms.CharField(
        label="Passwort bestätigen", 
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-3 py-2 input input-primary"
        })
    )
    lebensweisheit = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "w-full px-3 py-2 input input-primary"
        })
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 input input-primary"
            }),
            "first_name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 input input-primary"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 input input-primary"
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full px-3 py-2 input input-primary"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwörter stimmen nicht überein.")
        return cleaned
