from django.shortcuts import render, redirect, get_object_or_404
from .models import Course
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Material
from .models import Enrollment
from django.contrib.auth.models import User
from .models import TrainerApplication
from django.contrib import messages


@login_required
def student_courses(request):

    if request.user.profile.role != 'student':
        return HttpResponse("Only students allowed")

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course')

    # Prepare structured data
    course_data = []

    for enroll in enrollments:
        course = enroll.course
        materials = Material.objects.filter(course=course)

        course_data.append({
            'course': course,
            'materials': materials
        })

    return render(request, 'student_courses.html', {
        'course_data': course_data
    })


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

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return HttpResponse("Course not found")

    user = request.user
    role = user.profile.role

    # 🚫 STRICT ACCESS CONTROL
    if role == 'company':
        if course.company != user:
            return HttpResponse("Not allowed")

    elif role == 'trainer':
        # Trainer must be assigned to THIS course
        if course.trainer != user:
            return HttpResponse("You are not assigned to this course")

    else:
        return HttpResponse("Only company or assigned trainer allowed")

    if request.method == 'POST':

        title = request.POST.get('title')
        file = request.FILES.get('file')
        link = request.POST.get('link')

        # ❌ Must provide at least one
        if not file and not link:
            messages.error(request, "Provide file or link")
            return redirect(request.path)

        # 📁 File validation
        if file:
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
            ext = file.name.split('.')[-1].lower()

            if ext not in allowed_extensions:
                messages.error(request, "Only PDF or images allowed")
                return redirect(request.path)

            # 📏 Size limit (5MB)
            if file.size > 5 * 1024 * 1024:
                messages.error(request, "File too large (max 5MB)")
                return redirect(request.path)

        Material.objects.create(
            course=course,
            title=title,
            file=file,
            link=link,
            uploaded_by=user
        )

        messages.success(request, "Material uploaded successfully")

        # redirect based on role
        if role == 'company':
            return redirect('company_dashboard')
        else:
            return redirect('trainer_dashboard')

    return render(request, 'add_material.html', {'course': course})


def view_courses(request):

    courses = Course.objects.all()

    enrolled_ids = []

    if request.user.is_authenticated:
        enrolled_ids = Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)

    return render(request, 'view_courses.html', {
        'courses': courses,
        'enrolled_ids': enrolled_ids
    })


@login_required
def enroll_course(request, id):

    if request.user.profile.role != 'student':
        return HttpResponse("Only students allowed")

    course = Course.objects.get(id=id)

    # ✅ Prevent duplicate
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return HttpResponse("Already enrolled")

    total_students = Enrollment.objects.filter(course=course).count()

    if total_students >= course.max_students:
        return HttpResponse("Course is full")
    
    Enrollment.objects.create(
        student=request.user,
        course=course
    )

    return redirect('student_courses')   # ✅ better flow


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

    # 🔒 Only company allowed
    if request.user.profile.role != 'company':
        return HttpResponse("Only companies allowed")

    # ✅ Get course belonging to this company
    course = get_object_or_404(Course, id=course_id, company=request.user)

    # ✅ Approved trainers for this company
    approved_apps = TrainerApplication.objects.filter(
        company=request.user,
        status='approved'
    ).select_related('trainer')

    # ❌ Trainers already assigned to any course
    assigned_trainers = Course.objects.exclude(
        trainer=None
    ).values_list('trainer_id', flat=True)

    # ✅ Only available trainers
    available_apps = approved_apps.exclude(trainer__id__in=assigned_trainers)

    # 🟢 Handle form submission
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')

        if not trainer_id:
            return HttpResponse("No trainer selected")

        trainer = get_object_or_404(User, id=trainer_id)

        # 🔒 Ensure trainer is approved for this company
        if not approved_apps.filter(trainer=trainer).exists():
            return HttpResponse("Invalid trainer")

        # 🔒 Prevent assigning trainer to multiple courses
        if Course.objects.filter(trainer=trainer).exists():
            return HttpResponse("Trainer already assigned to another course")

        # ✅ Assign trainer
        course.trainer = trainer
        course.save()

        return redirect('company_dashboard')

    # 🟢 Render page
    return render(request, 'assign_trainer.html', {
        'course': course,
        'approved_apps': available_apps
    })
