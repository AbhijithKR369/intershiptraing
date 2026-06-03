from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Internship
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Application
from users.models import Notification


@login_required
def add_internship(request):
    if request.user.profile.role != 'company':
        return HttpResponse("Only companies allowed")

    if not request.user.profile.is_verified:
        return HttpResponse("Your account is pending verification. You cannot add internships.")

    if request.method == 'POST':
        fee = request.POST.get('fee')
        fee = float(fee) if fee else None

        start_date = request.POST.get('start_date') or None
        end_date = request.POST.get('end_date') or None
        application_deadline = request.POST.get('application_deadline') or None

        Internship.objects.create(
            company=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            location=request.POST['location'],
            fee=fee,
            start_date=start_date,
            end_date=end_date,
            application_deadline=application_deadline
        )
        return redirect('company_dashboard')

    return render(request, 'add_internship.html')


@login_required
def apply_internship(request, id):

    if request.user.profile.role != 'student':
        return render(request, 'message.html', {
            'title': 'Access Denied',
            'heading': 'Access Denied',
            'message': 'Only students are allowed to apply for internships.',
            'back_url': reverse('student_dashboard')
        })

    internship = Internship.objects.get(id=id)

    if Application.objects.filter(
        student=request.user, internship=internship
    ).exists():
        return render(request, 'message.html', {
            'title': 'Already Applied',
            'heading': 'Already Applied',
            'message': 'You have already applied for this internship.',
            'back_url': reverse('student_dashboard')
        })

    if request.method == 'POST':
        resume = request.FILES.get('resume')

        Application.objects.create(
            student=request.user,
            internship=internship,
            resume=resume
        )

        from django.urls import reverse
        Notification.objects.create(
            user=internship.company,
            message=f"New internship application from {request.user.username} for {internship.title}",
            link=reverse('view_applications')
        )

        return redirect('student_dashboard')

    return render(request, 'message.html', {
        'title': 'Invalid Request',
        'heading': 'Invalid Request',
        'message': 'The request method or parameters are invalid.',
        'back_url': reverse('student_dashboard')
    })

# student view internships


def view_internships(request):
    internships = Internship.objects.all()

    if request.user.is_authenticated:
        application_map = {a.internship_id: a.status for a in Application.objects.filter(student=request.user)}
        for i in internships:
            i.user_application_status = application_map.get(i.id, None)

    return render(request, 'view_internships.html', {
        'internships': internships
    })


# student apply internships


def view_applications(request):
    apps = Application.objects.filter(internship__company=request.user)
    return render(request, 'view_applications.html', {'apps': apps})


@login_required
def approve_application(request, id):

    app = Application.objects.get(id=id)

    if app.internship.company != request.user:
        return render(request, 'message.html', {
            'title': 'Unauthorized',
            'heading': 'Unauthorized',
            'message': 'You are not authorized to approve this application.',
            'back_url': '/'
        })

    # ✅ Approve
    app.status = 'approved'
    
    # ✅ Auto-pay if free
    if not app.internship.fee or app.internship.fee <= 0:
        app.is_paid = True

    # ✅ Assign roll number (per internship)
    count = Application.objects.filter(
        internship=app.internship,
        status='approved'
    ).count()

    app.roll_number = count + 1

    app.save()

    from django.urls import reverse
    Notification.objects.create(
        user=app.student,
        message=f"Your application for {app.internship.title} was approved",
        link=reverse('student_dashboard')
    )

    return redirect('view_applications')


@login_required
def reject_application(request, id):
    app = Application.objects.get(id=id)

    if app.internship.company != request.user:
        return render(request, 'message.html', {
            'title': 'Unauthorized',
            'heading': 'Unauthorized',
            'message': 'You are not authorized to reject this application.',
            'back_url': '/'
        })

    app.status = 'rejected'
    app.save()

    from django.urls import reverse
    Notification.objects.create(
        user=app.student,
        message=f"Your application for {app.internship.title} was rejected",
        link=reverse('student_dashboard')
    )

    return redirect('view_applications')


@login_required
def complete_internship(request, id):

    app = Application.objects.get(id=id, student=request.user)

    if app.status != 'approved':
        return render(request, 'message.html', {
            'title': 'Access Denied',
            'heading': 'Access Denied',
            'message': 'You cannot mark this internship as completed.',
            'back_url': reverse('student_dashboard')
        })

    app.completed = True
    app.save()

    return render(request, 'message.html', {
        'title': 'Internship Completed',
        'heading': 'Internship Completed',
        'message': 'You have successfully completed this internship.',
        'back_url': reverse('student_dashboard')
    })


@login_required
def download_certificate(request, id):

    app = Application.objects.get(id=id, student=request.user)

    if not app.certificate:
        return render(request, 'message.html', {
            'title': 'No Certificate',
            'heading': 'Certificate Unavailable',
            'message': 'No certificate has been uploaded for this internship yet.',
            'back_url': reverse('student_dashboard')
        })

    return redirect(app.certificate.url)
