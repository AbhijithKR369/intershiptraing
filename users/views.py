from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from courses.models import Enrollment, QuizResult
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from certificates.models import Certificate


def login_view(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # 🔁 Redirect based on role
            if user.profile.role == 'student':
                return redirect('student_dashboard')
            elif user.profile.role == 'company':
                return redirect('company_dashboard')
            elif user.profile.role == 'trainer':
                return redirect('trainer_dashboard')

        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


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
def student_dashboard(request):

    enrollments = Enrollment.objects.filter(
        student=request.user,
        status='approved'
    ).select_related('course')

    results = QuizResult.objects.filter(
        student=request.user
    ).select_related('batch', 'batch__course')

    # ✅ Only enrolled courses
    courses = [enroll.course for enroll in enrollments]

    # ✅ All certificates
    all_certs = Certificate.objects.filter(
        student=request.user
    ).select_related(
        'course__company', 'internship__company__profile'
    )

    notifications = request.user.notifications.all().order_by('-created_at')

    return render(request, 'student_dashboard.html', {
        'enrollments': enrollments,
        'courses': courses,
        'results': results,
        'all_certs': all_certs,
        'notifications': notifications
    })


@login_required
@user_passes_test(is_company)
def company_dashboard(request):

    enroll_requests = Enrollment.objects.filter(
        course__company=request.user,
        status='pending'
    ).select_related('student', 'student__profile', 'course')

    notifications = request.user.notifications.all().order_by('-created_at')

    return render(request, 'company_dashboard.html', {
        'enroll_requests': enroll_requests,
        'notifications': notifications
    })


@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):

    courses = request.user.trainer_courses.all()

    results = QuizResult.objects.filter(
        batch__course__in=courses
    ).select_related('student', 'batch', 'batch__course')

    notifications = request.user.notifications.all().order_by('-created_at')

    return render(request, 'trainer_dashboard.html', {
        'courses': courses,
        'results': results,
        'notifications': notifications
    })


def logout_view(request):
    logout(request)
    return redirect('login')


def dashboard(request):
    user = request.user

    if user.profile.role == 'student':
        return redirect('student_dashboard')
    elif user.profile.role == 'company':
        return redirect('company_dashboard')
    elif user.profile.role == 'trainer':
        return redirect('trainer_dashboard')


@login_required
def read_notification(request, notification_id):
    from .models import Notification
    from django.shortcuts import get_object_or_404
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('dashboard')

