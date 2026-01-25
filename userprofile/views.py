from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .forms import RegisterForm

# -------------------------
# Registrierung
# -------------------------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.is_active = True
            user.save()

            profile = user.userprofile
            profile.lebensweisheit = form.cleaned_data["lebensweisheit"]
            profile.save()

            # 🔥 HIER: automatisch einloggen
            login(request, user)

            messages.success(request, "Registrierung erfolgreich.")
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "userprofile/register.html", {"form": form})

# -------------------------
# Login
# -------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            return redirect("home")

        messages.error(request, "Login fehlgeschlagen. Prüfe Benutzername und Passwort.")

    return render(request, "userprofile/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def myaccount_view(request):
    return render(request, "userprofile/myaccount.html" )