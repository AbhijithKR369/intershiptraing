from django.shortcuts import render, redirect
from .models import Internship
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Application


@login_required
def add_internship(request):
    if request.method == 'POST':
        Internship.objects.create(
            company=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            location=request.POST['location']
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

        return redirect('student_dashboard')

    return HttpResponse("Invalid request")

# student view internships


def view_internships(request):
    internships = Internship.objects.all()

    applied_ids = []

    if request.user.is_authenticated:
        applied_ids = Application.objects.filter(
            student=request.user
        ).values_list('internship_id', flat=True)

    return render(request, 'view_internships.html', {
        'internships': internships,
        'applied_ids': applied_ids
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

    app.status = 'approved'
    app.save()

    return redirect('view_applications')


@login_required
def reject_application(request, id):
    app = Application.objects.get(id=id)

    if app.internship.company != request.user:
        return HttpResponse("Unauthorized")

    app.status = 'rejected'
    app.save()

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
