from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, QuizBatch
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Material, CourseMessage
from .models import Enrollment
from django.contrib.auth.models import User
from .models import TrainerApplication
from django.contrib import messages
from .models import Question, StudentAnswer
from .models import QuizResult, ReattemptRequest
from internships.models import Application
from certificates.models import Certificate
from certificates.utils import generate_certificate
from django.db.models import Q
from users.models import Notification


def quiz_batches(request, course_id):
    course = Course.objects.get(id=course_id)

    batches = QuizBatch.objects.filter(course=course, is_active=True)

    # ✅ FIX: get attempted batches correctly
    attempted_batches = QuizResult.objects.filter(
        student=request.user,
        batch__course=course
    ).values_list('batch_id', flat=True)

    return render(request, 'quiz_batches.html', {
        'course': course,
        'batches': batches,
        'attempted_batches': list(attempted_batches),  # important
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
    passed_final_map = {}

    # Course certificates
    for e in enrollments:
        cert = Certificate.objects.filter(
            student=e.student,
            course=e.course
        ).first()
        cert_map[e.id] = cert
        
        # Check if student passed final quiz
        passed = False
        final_results = QuizResult.objects.filter(
            student=e.student,
            batch__course=e.course,
            batch__is_final=True
        )
        for r in final_results:
            if r.total > 0 and r.score >= (r.total / 2):
                passed = True
                break
        passed_final_map[e.id] = passed

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
        'cert_map': cert_map,          # ✅ IMPORTANT
        'passed_final_map': passed_final_map
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
        fee = request.POST.get('fee')
        fee = float(fee) if fee else None

        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        application_deadline = request.POST.get('application_deadline') or None

        Course.objects.create(
            company=request.user,   # ✅ company owns course
            title=request.POST['title'],
            description=request.POST['description'],
            fee=fee,
            start_date=start_date,
            end_date=end_date,
            application_deadline=application_deadline
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
        class_link = request.POST.get('class_link')
        class_time = request.POST.get('class_time')

        # ❌ Must provide at least one
        if not file and not link and not class_link:
            messages.error(request, "Provide file, link, or class schedule")
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
            class_link=class_link,
            class_time=class_time if class_time else None,
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

    if request.user.is_authenticated:
        enrollment_map = {e.course_id: e.status for e in Enrollment.objects.filter(student=request.user)}
        for c in courses:
            c.user_enrollment_status = enrollment_map.get(c.id, None)

    return render(request, 'view_courses.html', {
        'courses': courses
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

            Notification.objects.create(
                user=course.company,
                message=f"New enrollment request from {request.user.username} for {course.title}",
                link="/dashboard/"
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

    Notification.objects.create(
        user=course.company,
        message=f"New enrollment request from {request.user.username} for {course.title}",
        link="/dashboard/"
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

        from django.urls import reverse
        Notification.objects.create(
            user=company,
            message=f"New trainer application from {request.user.username}",
            link=reverse('view_trainer_requests')
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

    Notification.objects.create(
        user=app.trainer,
        message=f"Your trainer application to {request.user.username} was approved",
        link="/dashboard/"
    )

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

    Notification.objects.create(
        user=enroll.student,
        message=f"Your enrollment for {enroll.course.title} was approved",
        link="/dashboard/"
    )

    return redirect('company_dashboard')


@login_required
def reject_enrollment(request, id):

    enroll = Enrollment.objects.get(id=id)

    if enroll.course.company != request.user:
        return HttpResponse("Not allowed")

    enroll.status = 'rejected'
    enroll.save()

    Notification.objects.create(
        user=enroll.student,
        message=f"Your enrollment for {enroll.course.title} was rejected",
        link="/dashboard/"
    )

    return redirect('company_dashboard')


@login_required
def reject_trainer(request, id):
    app = TrainerApplication.objects.get(id=id)

    if app.company != request.user:
        return HttpResponse("Unauthorized")

    app.status = 'rejected'
    app.save()

    Notification.objects.create(
        user=app.trainer,
        message=f"Your trainer application to {request.user.username} was rejected",
        link="/dashboard/"
    )

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

        Notification.objects.create(
            user=trainer,
            message=f"You have been assigned to course {course.title} by {request.user.username}",
            link="/dashboard/"
        )

        return redirect('company_dashboard')

    # 🟢 Render page
    return render(request, 'assign_trainer.html', {
        'course': course,
        'approved_apps': available_apps
    })


@login_required
def create_quiz_batch(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user != course.company and request.user != course.trainer:
        return HttpResponse("Not allowed")

    if request.method == "POST":
        title = request.POST.get('title')
        num_questions = int(request.POST.get('number_of_questions', 10))
        time_limit = int(request.POST.get('time_limit', 15))
        deadline = request.POST.get('deadline') or None
        is_final = request.POST.get('is_final') == 'on'

        if is_final:
            if request.user.profile.role != 'company':
                return HttpResponse("Only company can create final quiz")
            if QuizBatch.objects.filter(course=course, is_final=True).exists():
                return HttpResponse("Final quiz already exists")

        batch = QuizBatch.objects.create(
            course=course,
            title=title,
            number_of_questions=num_questions,
            time_limit=time_limit,
            deadline=deadline,
            is_final=is_final
        )
        return redirect('add_question', batch_id=batch.id)

    return render(request, 'create_quiz_batch.html', {'course': course})


@login_required
def add_question(request, batch_id):
    batch = get_object_or_404(QuizBatch, id=batch_id)
    course = batch.course

    if request.user != course.company and request.user != course.trainer:
        return HttpResponse("Not allowed")

    if request.method == "POST":
        # Form should submit multiple questions
        for i in range(1, batch.number_of_questions + 1):
            q_text = request.POST.get(f'question_{i}')
            opt1 = request.POST.get(f'opt1_{i}')
            opt2 = request.POST.get(f'opt2_{i}')
            opt3 = request.POST.get(f'opt3_{i}')
            opt4 = request.POST.get(f'opt4_{i}')
            correct = request.POST.get(f'correct_{i}')

            if q_text and opt1 and opt2 and opt3 and opt4 and correct:
                Question.objects.create(
                    batch=batch,
                    question_text=q_text,
                    option1=opt1,
                    option2=opt2,
                    option3=opt3,
                    option4=opt4,
                    correct_option=correct
                )
        if request.user.profile.role == 'company':
            return redirect('company_dashboard')
        else:
            return redirect('trainer_dashboard')

    return render(request, 'add_question.html', {
        'batch': batch,
        'course': course,
        'range': range(1, batch.number_of_questions + 1)
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

    # Deadline check
    import django.utils.timezone as timezone
    if batch.deadline and timezone.now() > batch.deadline:
        return HttpResponse("Deadline has passed")

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


@login_required
def course_chat(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    role = user.profile.role

    # Access control
    has_access = False
    if role == 'company' and course.company == user:
        has_access = True
    elif role == 'trainer' and course.trainer == user:
        has_access = True
    elif role == 'student':
        if Enrollment.objects.filter(student=user, course=course, status='approved').exists():
            has_access = True

    if not has_access:
        return HttpResponse("You do not have access to this course's chat.", status=403)

    return render(request, 'course_chat.html', {'course': course})

@login_required
def request_reattempt(request, batch_id):
    batch = get_object_or_404(QuizBatch, id=batch_id)
    if not batch.is_final:
        return HttpResponse("Re-attempts only available for final quizzes")
    
    # Check if a request already exists
    if ReattemptRequest.objects.filter(student=request.user, batch=batch).exists():
        return HttpResponse("Request already submitted")
        
    ReattemptRequest.objects.create(student=request.user, batch=batch)

    from django.urls import reverse
    Notification.objects.create(
        user=batch.course.company,
        message=f"New re-attempt request from {request.user.username} for {batch.course.title}",
        link=reverse('view_reattempts')
    )
    if batch.course.trainer:
        Notification.objects.create(
            user=batch.course.trainer,
            message=f"New re-attempt request from {request.user.username} for {batch.course.title}",
            link=reverse('view_reattempts')
        )

    return redirect('review_quiz', batch_id=batch.id)

@login_required
def view_reattempts(request):
    if request.user.profile.role not in ['company', 'trainer']:
        return HttpResponse("Not allowed")
        
    requests = ReattemptRequest.objects.filter(
        batch__course__company=request.user, 
        status='pending'
    )
    # If trainer, only show for assigned courses
    if request.user.profile.role == 'trainer':
        requests = ReattemptRequest.objects.filter(
            batch__course__trainer=request.user,
            status='pending'
        )
        
    return render(request, 'reattempt_requests.html', {'requests': requests})

@login_required
def handle_reattempt(request, request_id, action):
    req = get_object_or_404(ReattemptRequest, id=request_id)
    
    # Validation
    if request.user.profile.role == 'company' and req.batch.course.company != request.user:
        return HttpResponse("Not allowed")
    if request.user.profile.role == 'trainer' and req.batch.course.trainer != request.user:
        return HttpResponse("Not allowed")
        
    if action == 'approve':
        req.status = 'approved'
        # Delete previous results and answers
        QuizResult.objects.filter(student=req.student, batch=req.batch).delete()
        StudentAnswer.objects.filter(student=req.student, question__batch=req.batch).delete()
    elif action == 'reject':
        req.status = 'rejected'
        
    req.save()

    status_msg = "approved" if req.status == 'approved' else "rejected"
    Notification.objects.create(
        user=req.student,
        message=f"Your re-attempt request for {req.batch.course.title} was {status_msg}",
        link="/dashboard/"
    )

    return redirect('view_reattempts')




@login_required
def get_course_messages(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    role = user.profile.role

    # Access control
    has_access = False
    if role == 'company' and course.company == user:
        has_access = True
    elif role == 'trainer' and course.trainer == user:
        has_access = True
    elif role == 'student':
        if Enrollment.objects.filter(student=user, course=course, status='approved').exists():
            has_access = True

    if not has_access:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages = CourseMessage.objects.filter(course=course).order_by('timestamp')
    data = []
    for msg in messages:
        sender_role = msg.sender.profile.role.capitalize()
        # Fallback to username if name is not set
        sender_name = msg.sender.username
        if msg.sender.profile.role == 'student' and msg.sender.profile.full_name:
            sender_name = msg.sender.profile.full_name
        elif msg.sender.profile.role == 'company' and msg.sender.profile.company_name:
            sender_name = msg.sender.profile.company_name
            
        data.append({
            'id': msg.id,
            'sender_name': sender_name,
            'sender_role': sender_role,
            'is_me': msg.sender == user,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%I:%M %p')
        })

    return JsonResponse({'messages': data})


@login_required
def send_course_message(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        role = user.profile.role

        # Access control
        has_access = False
        if role == 'company' and course.company == user:
            has_access = True
        elif role == 'trainer' and course.trainer == user:
            has_access = True
        elif role == 'student':
            if Enrollment.objects.filter(student=user, course=course, status='approved').exists():
                has_access = True

        if not has_access:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        content = request.POST.get('content')
        if content and content.strip():
            CourseMessage.objects.create(
                course=course,
                sender=user,
                content=content.strip()
            )

            from django.urls import reverse
            chat_link = reverse('course_chat', kwargs={'course_id': course.id})
            
            users_to_notify = []
            if course.company != user:
                users_to_notify.append(course.company)
            if course.trainer and course.trainer != user:
                users_to_notify.append(course.trainer)
            
            enrolled_students = User.objects.filter(
                enrollment__course=course,
                enrollment__status='approved'
            ).exclude(id=user.id)
            users_to_notify.extend(enrolled_students)

            for u in users_to_notify:
                Notification.objects.create(
                    user=u,
                    message=f"New message in {course.title} from {user.username}",
                    link=chat_link
                )

            return JsonResponse({'status': 'ok'})
        return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
