from django.shortcuts import render, redirect
from .models import Course
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Material
from .models import Enrollment
from django.contrib.auth.models import User
from .models import TrainerApplication


@login_required
def add_course(request):

    # ✅ Only company allowed
    if request.user.profile.role != 'company':
        return HttpResponse("Only companies allowed")

    if request.method == 'POST':
        Course.objects.create(
            company=request.user,   # ✅ company owns course
            title=request.POST['title'],
            description=request.POST['description']
        )
        return redirect('company_dashboard')

    return render(request, 'add_course.html')


@login_required
def add_material(request, course_id):

    course = Course.objects.get(id=course_id)

    # ✅ Permission restriction (VERY IMPORTANT)
    if request.user != course.company and request.user != course.trainer:
        return HttpResponse("Not allowed")

    if request.method == 'POST':
        Material.objects.create(
            course=course,
            title=request.POST['title'],
            file=request.FILES.get('file'),
            link=request.POST.get('link'),
            uploaded_by=request.user   # ✅ IMPORTANT (you missed this)
        )
        return redirect('trainer_dashboard')

    return render(request, 'add_material.html', {'course': course})


def view_courses(request):
    courses = Course.objects.all()
    return render(request, 'view_courses.html', {'courses': courses})


@login_required
def enroll_course(request, id):

    if request.user.profile.role != 'student':
        return HttpResponse("Only students allowed")

    course = Course.objects.get(id=id)

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return HttpResponse("Already enrolled")

    Enrollment.objects.create(
        student=request.user,
        course=course
    )

    return redirect('student_dashboard')


@login_required
def trainer_apply_list(request):

    # Only trainer allowed
    if request.user.profile.role != 'trainer':
        return HttpResponse("Only trainers allowed")

    # Get all companies
    companies = User.objects.filter(profile__role='company')

    # Get already applied company IDs
    applied_ids = TrainerApplication.objects.filter(
        trainer=request.user
    ).values_list('company_id', flat=True)

    return render(request, 'trainer_apply_list.html', {
        'companies': companies,
        'applied_ids': applied_ids
    })


@login_required
def apply_company(request, company_id):

    if request.user.profile.role != 'trainer':
        return HttpResponse("Only trainers allowed")

    company = User.objects.get(id=company_id)

    if TrainerApplication.objects.filter(
        trainer=request.user, company=company
    ).exists():
        return HttpResponse("Already applied")

    if request.method == 'POST':
        resume = request.FILES.get('resume')

        TrainerApplication.objects.create(
            trainer=request.user,
            company=company,
            resume=resume
        )

        return redirect('trainer_apply_list')

    return HttpResponse("Invalid request")


@login_required
def view_trainer_requests(request):

    if request.user.profile.role != 'company':
        return HttpResponse("Only companies allowed")

    apps = TrainerApplication.objects.filter(company=request.user)

    return render(request, 'trainer_requests.html', {'apps': apps})


@login_required
def approve_trainer(request, id):
    app = TrainerApplication.objects.get(id=id)

    if app.company != request.user:
        return HttpResponse("Unauthorized")

    app.status = 'approved'
    app.save()

    return redirect('view_trainer_requests')


@login_required
def reject_trainer(request, id):
    app = TrainerApplication.objects.get(id=id)

    if app.company != request.user:
        return HttpResponse("Unauthorized")

    app.status = 'rejected'
    app.save()

    return redirect('view_trainer_requests')


@login_required
def assign_trainer(request, course_id):

    # Only company allowed
    if request.user.profile.role != 'company':
        return HttpResponse("Only companies allowed")

    course = Course.objects.get(id=course_id, company=request.user)

    # Get only approved trainers for this company
    approved_apps = TrainerApplication.objects.filter(
        company=request.user,
        status='approved'
    ).select_related('trainer')

    if request.method == 'POST':
        trainer_id = request.POST.get('trainer_id')

        trainer = User.objects.get(id=trainer_id)

        # Extra safety: ensure trainer belongs to approved list
        if not approved_apps.filter(trainer=trainer).exists():
            return HttpResponse("Invalid trainer")

        course.trainer = trainer
        course.save()

        return redirect('company_dashboard')

    return render(request, 'assign_trainer.html', {
        'course': course,
        'approved_apps': approved_apps
    })
