from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test


def dashboard(request):
    return HttpResponse("Login Successful! Welcome to Dashboard")


def register(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST.get('confirm_password')

        # ✅ Password check FIRST
        if password != confirm_password:
            return HttpResponse("Passwords do not match")

        # ✅ Username exists check
        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists")

        # ✅ Now create user
        user = User.objects.create_user(username=username, password=password)

        profile = user.profile
        profile.role = request.POST['role']
        profile.domain = request.POST['domain']

        profile.full_name = request.POST.get('full_name')
        profile.email = request.POST.get('email')
        profile.phone = request.POST.get('phone')

        # Student
        profile.college_name = request.POST.get('college')
        profile.department = request.POST.get('department')

        # Company
        profile.company_name = request.POST.get('company_name')
        profile.location = request.POST.get('location')

        # Trainer
        profile.qualification = request.POST.get('qualification')
        profile.place = request.POST.get('place')

        profile.save()

        return redirect('login')

    return render(request, 'register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            role = user.profile.role

            if role == 'student':
                return redirect('student_dashboard')
            elif role == 'company':
                return redirect('company_dashboard')
            elif role == 'trainer':
                return redirect('trainer_dashboard')

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


def is_student(user):
    return user.profile.role == 'student'


def is_company(user):
    return user.profile.role == 'company'


def is_trainer(user):
    return user.profile.role == 'trainer'


@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    return render(request, 'student_dashboard.html')


@login_required
@user_passes_test(is_company)
def company_dashboard(request):
    return render(request, 'company_dashboard.html')


@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    return render(request, 'trainer_dashboard.html')
