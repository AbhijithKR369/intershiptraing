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

    Application.objects.create(
        student=request.user,
        internship=internship
    )

    return redirect('student_dashboard')

# student view internships


def view_internships(request):
    internships = Internship.objects.all()
    return render(
        request,
        'view_internships.html',
        {'internships': internships}
    )


# student apply internships


def view_applications(request):
    apps = Application.objects.filter(internship__company=request.user)
    return render(request, 'view_applications.html', {'apps': apps})
