# Create your views here.
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from rest_framework import generics
import logging

from .models import CeleryTask
from .serializers import CeleryTaskSerializer
from .forms import SyncForm

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def index(request):
    return render(request, "home.html", {})


def tasks(request):
    return render(request, "tasks.html", {})


def sync(request):
    if request.method == "POST":
        form = SyncForm(request.POST)
        logger.debug("POST data:", request.POST)
        logger.debug("Form errors:", form.errors)
        if form.is_valid():
            # Process the form data, e.g., call Celery task
            # Access form.cleaned_data to get the input values
            # Example: form.cleaned_data['source'], form.cleaned_data['destination']
            # Call Celery task here with the input data

            return render(request, "sync.html", {"form": form, "success": True})
    else:
        form = SyncForm()

    logger.debug("Form initial data:", form.initial)
    logger.debug("Form fields:", form.fields)

    return render(request, "sync.html", {"form": form})


class CeleryTaskList(generics.ListCreateAPIView):
    queryset = CeleryTask.objects.all()
    serializer_class = CeleryTaskSerializer


class CeleryTaskDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CeleryTask.objects.all()
    serializer_class = CeleryTaskSerializer


class CustomLoginView(LoginView):
    template_name = "login.html"
    success_url = "/"
