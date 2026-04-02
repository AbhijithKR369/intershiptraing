from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, QuizBatch
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Material
from .models import Enrollment
from django.contrib.auth.models import User
from .models import TrainerApplication
from django.contrib import messages
from .models import Question, StudentAnswer
from .models import QuizResult
from internships.models import Application
from certificates.models import Certificate
from certificates.utils import generate_certificate
from django.db.models import Q


def quiz_batches(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    batches = QuizBatch.objects.filter(course=course)

    return render(request, 'quiz_batches.html', {
        'course': course,
        'batches': batches
    })

@login_required
def manage_certificates(request):

    if request.user.profile.role != 'company':
        return HttpResponse("Not allowed")

    # 🔎 Filters
    search = request.GET.get('q')
    course_id = request.GET.get('course')
    internship_id = request.GET.get('internship')

    # 📚 Course enrollments
    enrollments = Enrollment.objects.filter(
        course__company=request.user,
        status='approved'
    ).select_related('student', 'course').order_by('joined_date')

    # 💼 Internship applications
    applications = Application.objects.filter(
        internship__company=request.user,
        status='approved'
    ).select_related('student', 'internship').order_by('joined_date')

    # 🔍 Search
    if search:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search) |
            Q(roll_number__icontains=search)
        )
        applications = applications.filter(
            Q(student__username__icontains=search) |
            Q(roll_number__icontains=search)
        )

    # 📚 Filter by course
    if course_id:
        enrollments = enrollments.filter(course_id=course_id)

    # 💼 Filter by internship
    if internship_id:
        applications = applications.filter(internship_id=internship_id)

    # 📤 Upload / Replace handling
    if request.method == "POST":
        file = request.FILES.get('certificate')

        enroll_id = request.POST.get('enroll_id')
        app_id = request.POST.get('app_id')

        # 📚 Course certificate
        if enroll_id and file:
            enroll = Enrollment.objects.get(id=enroll_id)

            Certificate.objects.update_or_create(
                student=enroll.student,
                course=enroll.course,
                defaults={
                    'file': file,
                    'is_manual': True
                }
            )

        # 💼 Internship certificate
        if app_id and file:
            app = Application.objects.get(id=app_id)

            Certificate.objects.update_or_create(
                student=app.student,
                internship=app.internship,
                defaults={
                    'file': file,
                    'is_manual': True
                }
            )

    # 🧠 Build certificate map (NO duplicates in UI)
    cert_map = {}

    # Course certificates
    for e in enrollments:
        cert = Certificate.objects.filter(
            student=e.student,
            course=e.course
        ).first()
        cert_map[e.id] = cert

    # Internship certificates
    for a in applications:
        cert = Certificate.objects.filter(
            student=a.student,
            internship=a.internship
        ).first()
        cert_map[a.id] = cert

    # Dropdown data
    courses = Enrollment.objects.filter(
        course__company=request.user
    ).values('course__id', 'course__title').distinct()

    internships = Application.objects.filter(
        internship__company=request.user
    ).values('internship__id', 'internship__title').distinct()

    return render(request, 'manage_certificates.html', {
        'enrollments': enrollments,
        'applications': applications,
        'courses': courses,
        'internships': internships,
        'cert_map': cert_map   # ✅ IMPORTANT
    })


@login_required
def student_courses(request):

    if request.user.profile.role != 'student':
        return HttpResponse("Only students allowed")

    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course')

    # ✅ ADDED HERE
    certificates = Certificate.objects.filter(
        student=request.user
    )

    course_data = []

    for enroll in enrollments:
        course = enroll.course
        materials = Material.objects.filter(course=course)

        course_data.append({
            'course': course,
            'materials': materials
        })

    return render(request, 'student_courses.html', {
        'course_data': course_data,
        'certificates': certificates   # ✅ ADDED HERE
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

    # ✅ Check internship approval with this company
    has_approved_internship = Application.objects.filter(
        student=request.user,
        internship__company=course.company,
        status='approved'
    ).exists()

    # ✅ If NOT approved → require resume
    if not has_approved_internship:

        if request.method == 'POST':
            resume = request.FILES.get('resume')

            Enrollment.objects.create(
                student=request.user,
                course=course,
                resume=resume,
                status='pending'
            )

            return HttpResponse("Request sent. Wait for approval")

        return render(request, 'upload_resume.html', {'course': course})

    # ✅ Already approved → direct enrollment request
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return HttpResponse("Already requested")

    Enrollment.objects.create(
        student=request.user,
        course=course,
        status='pending'
    )

    return HttpResponse("Enrollment request sent")


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
def approve_enrollment(request, id):

    enroll = Enrollment.objects.get(id=id)

    if enroll.course.company != request.user:
        return HttpResponse("Not allowed")

    # ✅ Set status
    enroll.status = 'approved'

    # ✅ Assign roll number (per course)
    count = Enrollment.objects.filter(
        course=enroll.course,
        status='approved'
    ).count()

    enroll.roll_number = count + 1

    enroll.save()

    return redirect('company_dashboard')


@login_required
def reject_enrollment(request, id):

    enroll = Enrollment.objects.get(id=id)

    if enroll.course.company != request.user:
        return HttpResponse("Not allowed")

    enroll.status = 'rejected'
    enroll.save()

    return redirect('company_dashboard')


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


@login_required
def add_question(request, course_id):

    course = Course.objects.get(id=course_id)

    if request.user != course.company and request.user != course.trainer:
        return HttpResponse("Not allowed")

    message = ""

    # ✅ Get latest batch (not using is_active anymore)
    batch = QuizBatch.objects.filter(course=course).last()

    if request.method == "POST":

        # ✅ Create new batch
        if 'new_batch' in request.POST:

            batch_type = request.POST.get('new_batch')  # 👈 key change

            existing_final = QuizBatch.objects.filter(
                course=course,
                is_final=True
            ).exists()

            is_final = False

            # ✅ Handle FINAL quiz creation properly
            if batch_type == 'final':

                if request.user.profile.role != 'company':
                    return HttpResponse("Only company can create final quiz")

                if existing_final:
                    return HttpResponse("Final quiz already exists")

                is_final = True

            quiz_count = QuizBatch.objects.filter(course=course).count() + 1

            batch = QuizBatch.objects.create(
                course=course,
                title=f"Quiz {quiz_count}",
                is_final=is_final
            )

            message = f"New batch created: {batch.title}"

        # ✅ Add question (ONLY if question exists)
        elif 'question' in request.POST:

            Question.objects.create(
                batch=batch,
                question_text=request.POST.get('question'),
                option1=request.POST.get('opt1'),
                option2=request.POST.get('opt2'),
                option3=request.POST.get('opt3'),
                option4=request.POST.get('opt4'),
                correct_option=request.POST.get('correct')
            )

            message = f"Question added to {batch.title}"

    questions = batch.questions.all() if batch else []

    return render(request, 'add_question.html', {
        'course': course,
        'message': message,
        'count': len(questions),
        'batch': batch
    })


@login_required
def take_quiz(request, batch_id):

    batch = QuizBatch.objects.get(id=batch_id)
    course = batch.course

    # enrollment check
    if not Enrollment.objects.filter(
        student=request.user, course=course
    ).exists():
        return HttpResponse("Enroll first")

    # ✅ Final quiz lock
    if batch.is_final:

        previous_batches = QuizBatch.objects.filter(
            course=course,
            is_final=False
        )

        attempted_count = QuizResult.objects.filter(
            student=request.user,
            batch__in=previous_batches
        ).count()

        if attempted_count < previous_batches.count():
            return HttpResponse("Complete all previous quizzes first")

    # prevent reattempt
    if QuizResult.objects.filter(student=request.user, batch=batch).exists():
        return redirect('review_quiz', batch_id=batch.id)

    questions = batch.questions.all()

    return render(request, 'quiz.html', {
        'questions': questions,
        'batch': batch,
        'course': course
    })


@login_required
def submit_quiz(request, batch_id):

    if request.user.profile.role != 'student':
        return HttpResponse("Only students allowed")

    batch = QuizBatch.objects.get(id=batch_id)
    course = batch.course

    # Ensure enrolled
    if not Enrollment.objects.filter(
        student=request.user,
        course=course
    ).exists():
        return HttpResponse("Enroll first")

    questions = batch.questions.all()

    # Prevent reattempt
    if QuizResult.objects.filter(
        student=request.user,
        batch=batch
    ).exists():
        return HttpResponse("Already submitted this quiz")

    score = 0

    for q in questions:
        selected = request.POST.get(str(q.id))

        if not selected:
            continue

        selected = int(selected)

        StudentAnswer.objects.update_or_create(
            student=request.user,
            question=q,
            defaults={'selected_option': selected}
        )

        if selected == q.correct_option:
            score += 1

    total = questions.count()

    # Save result
    QuizResult.objects.update_or_create(
        student=request.user,
        batch=batch,
        defaults={
            'score': score,
            'total': total
        }
    )

    # Certificate (final only)
    if batch.is_final and score >= (total / 2):

        cert_exists = Certificate.objects.filter(
            student=request.user,
            course=course
        ).exists()

        if not cert_exists:

            file_path = generate_certificate(
                student_name=request.user.username,
                course_name=course.title,
                score=score,
                total=total,
                company_name=course.company.username
            )

            Certificate.objects.get_or_create(
                student=request.user,
                course=course,
                defaults={
                    'file': file_path,
                    'is_manual': False   # ✅ AUTO
                }
            )

    # Get all results
    results = QuizResult.objects.filter(
        student=request.user,
        batch__course=course
    ).select_related('batch')

    return render(request, 'result.html', {
        'score': score,
        'total': total,
        'course': course,
        'results': results
    })


@login_required
def view_results(request, course_id):

    course = Course.objects.get(id=course_id)

    # ✅ Only company or trainer
    if request.user != course.company and request.user != course.trainer:
        return HttpResponse("Not allowed")

    results = QuizResult.objects.filter(
        batch__course=course
    ).select_related('student', 'batch')

    return render(request, 'result.html', {
        'course': course,
        'results': results
    })


@login_required
def course_quizzes(request, course_id):

    course = Course.objects.get(id=course_id)

    batches = QuizBatch.objects.filter(course=course).order_by('id')

    attempted_batches = QuizResult.objects.filter(
        student=request.user,
        batch__course=course
    ).values_list('batch_id', flat=True)

    certificates = Certificate.objects.filter(
        student=request.user,
        course=course
    )

    return render(request, 'quiz_batches.html', {
        'course': course,
        'batches': batches,
        'attempted_batches': list(attempted_batches),
        'certificates': certificates
    })


@login_required
def review_quiz(request, batch_id):

    batch = QuizBatch.objects.get(id=batch_id)
    questions = batch.questions.all()

    answers = StudentAnswer.objects.filter(
        student=request.user,
        question__batch=batch
    )

    answer_map = {a.question_id: a.selected_option for a in answers}

    return render(request, 'review.html', {
        'questions': questions,
        'answers': answer_map,
        'batch': batch
    })
