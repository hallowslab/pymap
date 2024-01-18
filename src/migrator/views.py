# Create your views here.
import logging
from typing import List
from os import mkdir
from os.path import isdir
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.conf import settings
from rest_framework import generics


from .models import CeleryTask
from .serializers import CeleryTaskSerializer
from .forms import SyncForm
from .tasks import call_system
from core.pymap_core import ScriptGenerator

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "home.html", {})


def tasks(request):
    return render(request, "tasks.html", {})


def sync(request):
    if request.method == "POST":
        form = SyncForm(request.POST)
        # logger.debug("POST data: %s", request.POST)
        logger.error("Form errors: %s", form.errors)
        if form.is_valid():
            # Process the form data, e.g., call Celery task
            # Access form.cleaned_data to get the input values
            # Example: form.cleaned_data['source'], form.cleaned_data['destination']
            # Call Celery task here with the input data
            source: str = form.cleaned_data["source"]
            destination: str = form.cleaned_data["destination"]
            input_text: List[str] = form.cleaned_data["input_text"].strip().split("\n")
            additional_arguments: str = form.cleaned_data["additional_arguments"]
            dry_run: bool = form.cleaned_data["dry_run"]
            config = settings.PYMAP_SETTINGS
            user = request.user.username
            logger.debug(
                "USER: %s requested a sync for %s -> %s", user, source, destination
            )
            logger.debug(
                "\nSource: %s\nDestination: %s\nAdditional arguments: %s\nDry run: %s",
                source,
                destination,
                additional_arguments,
                dry_run,
            )
            gen = ScriptGenerator(
                source,
                destination,
                extra_args=additional_arguments,
                config=config,
                dry_run=dry_run,
            )
            content = gen.process_strings(input_text)

            # TODO: Strip out passwords before logging commands
            # logger.debug(
            #     "Received the following output from generator:\n %s", content
            # )

            task = call_system.delay(content)
            root_log_directory = config.get("LOGDIR", "/var/log/pymap")
            log_directory = f"{root_log_directory}/{task.id}"
            ctask = CeleryTask(
                task_id=task.id,
                source=source,
                destination=destination,
                log_path=log_directory,
                n_accounts=len(content),
                domains=gen.domains,
                owner_username=user,
            )
            ctask.save()
            if not isdir(log_directory):
                mkdir(log_directory)
            else:
                logger.warning(
                    "Directory: %s seems to already exist, we might be writting over files",
                    log_directory,
                )
                # TODO: Add logic for when this conflict might happen
            logger.info("Starting background task with ID: %s", task.id)

            # logger.debug("INPUT:\n%s", input_text)
            logger.debug("CONTENT:\n%s", content)

            return render(request, "sync.html", {"form": form, "success": True})
    else:
        form = SyncForm()

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
