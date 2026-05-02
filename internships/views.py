from django.shortcuts import render, redirect
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
        return HttpResponse("Only students can apply")

    internship = Internship.objects.get(id=id)

    if Application.objects.filter(
        student=request.user, internship=internship
    ).exists():
        return HttpResponse("Already applied")

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

    return HttpResponse("Invalid request")

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
        return HttpResponse("Unauthorized")

    # ✅ Approve
    app.status = 'approved'

    # ✅ Assign roll number (per internship)
    count = Application.objects.filter(
        internship=app.internship,
        status='approved'
    ).count()

    app.roll_number = count + 1

    app.save()

    Notification.objects.create(
        user=app.student,
        message=f"Your application for {app.internship.title} was approved",
        link="/dashboard/"
    )

    return redirect('view_applications')


@login_required
def reject_application(request, id):
    app = Application.objects.get(id=id)

    if app.internship.company != request.user:
        return HttpResponse("Unauthorized")

    app.status = 'rejected'
    app.save()

    Notification.objects.create(
        user=app.student,
        message=f"Your application for {app.internship.title} was rejected",
        link="/dashboard/"
    )

    return redirect('view_applications')


@login_required
def complete_internship(request, id):

    app = Application.objects.get(id=id, student=request.user)

    if app.status != 'approved':
        return HttpResponse("Not allowed")

    app.completed = True
    app.save()

    return HttpResponse("Internship completed")


@login_required
def download_certificate(request, id):

    app = Application.objects.get(id=id, student=request.user)

    if not app.certificate:
        return HttpResponse("No certificate uploaded")

    return redirect(app.certificate.url)
