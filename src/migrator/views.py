# Create your views here.
import logging
from subprocess import PIPE, Popen, TimeoutExpired
from typing import List
from os import mkdir, listdir
from os.path import isdir, isfile, join
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from rest_framework import generics
from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import CeleryTask
from .serializers import CeleryTaskSerializer
from .forms import SyncForm
from .tasks import call_system
from .utilites.helpers import get_logs_status
from core.pymap_core import ScriptGenerator

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "home.html", {})


def tasks(request):
    return render(request, "tasks.html", {})


def task_details(request, task_id):
    return render(request, "task_details.html", {"task_id": task_id})


def log_details(request, task_id, log_file):
    return render(
        request, "log_details.html", {"task_id": task_id, "log_file": log_file}
    )


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
            user = request.user
            logger.info(
                "USER: %s requested a sync for %s -> %s",
                user.username,
                source,
                destination,
            )
            logger.debug(
                "\nSource: %s\nDestination: %s\nAdditional arguments: %s\nDry run: %s",
                source,
                destination,
                additional_arguments,
                dry_run,
            )
            # TODO: Strip out passwords before logging commands
            # logger.debug(
            #     "Received the following input from client:\n %s", input_text
            # )
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
            logger.info(
                "Starting background task with ID: %s from User: %s",
                task.id,
                user.username,
            )

            # Don't forget to save the task id and respective inputs to the database
            root_log_directory = config.get("LOGDIR", "/var/log/pymap")
            log_directory = f"{root_log_directory}/{task.id}"
            domains = ", ".join(gen.domains)
            ctask = CeleryTask(
                task_id=task.id,
                source=source,
                destination=destination,
                log_path=log_directory,
                n_accounts=len(content),
                domains=domains,
                owner=user,
            )
            ctask.save()

            # Check for existence of log directory
            if not isdir(log_directory):
                mkdir(log_directory)
            else:
                # TODO: Add logic for when this conflict might happen
                logger.warning(
                    "Directory: %s seems to already exist, we might be writting over files",
                    log_directory,
                )

            target_url = reverse("tasks")
            return redirect(target_url)
    else:
        form = SyncForm()

    return render(request, "sync.html", {"form": form})


## CLASSES
class DownloadLog(View):
    def get(self, request, task_id, log_file):
        logger.debug("Got request for a download for: %s/%s", task_id, log_file)
        config = settings.PYMAP_SETTINGS
        log_directory = config.get("LOGDIR")

        log_path = join(log_directory, task_id, log_file)

        # Check if the file exists
        if isfile(log_path):
            with open(log_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="text/plain")
                response["Content-Disposition"] = f'attachment; filename="{log_file}"'
                return response
        else:
            return HttpResponse("Log file not found.", status=404)


class CeleryTaskList(generics.ListCreateAPIView):
    """
    API endpoint to fetch all tasks
    """

    # Here we obtain a queryset from the model itself
    queryset = CeleryTask.objects.all()
    serializer_class = CeleryTaskSerializer

    def list(self, request, *args, **kwargs):
        # Handle DataTables parameters
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        # Filtering based on search value
        queryset = self.filter_queryset(self.get_queryset())
        if search_value:
            queryset = queryset.filter(source__icontains=search_value)

        # Total records without filtering
        total_records = self.get_queryset().count()

        # Total records after filtering
        total_filtered_records = queryset.count()

        # Paginate the queryset
        queryset = queryset[start : start + length]

        # Serialize the queryset
        serializer = CeleryTaskSerializer(queryset, many=True)

        # Prepare the response data
        response_data = {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered_records,
            "data": serializer.data,
        }

        return JsonResponse(response_data, safe=False)


class CeleryTaskDetails(APIView):
    """
    API endpoint to fetch all jobs inside a task
    """

    def get(self, request, task_id):
        config = settings.PYMAP_SETTINGS
        log_directory = config.get("LOG_DIRECTORY", "/var/log/pymap")

        try:
            # Handle DataTables parameters
            draw = int(request.GET.get("draw", 1))
            start = int(request.GET.get("start", 0))
            length = int(request.GET.get("length", 10))
            search_value = request.GET.get("search[value]", "")

            # Since this data does not get stored we need to generate it
            logs_dir = join(log_directory, str(task_id))
            all_logs = [
                get_logs_status(logs_dir, f)
                for f in listdir(logs_dir)
                if isfile(join(logs_dir, f))
            ]

            # Filtering based on search value
            # TODO: Pretty sure this is not correct
            if search_value:
                all_logs = [
                    log
                    for log in all_logs
                    if search_value.lower() in log["log_file"].lower()
                ]

            total_records = len(all_logs)

            # Paginate the data
            paginated_logs = all_logs[start : start + length]

            return Response(
                {
                    "draw": draw,
                    "recordsTotal": total_records,
                    "recordsFiltered": total_records,
                    "data": paginated_logs,
                },
                status=200,
            )

        except ValidationError:
            return Response(
                {"error": "DJANGO:Failed to serialize data", "data": all_logs},
                status=500,
            )
        except FileNotFoundError:
            return Response(
                {
                    "error": "DJANGO:The directory does not exist on the system",
                    "data": logs_dir,
                }
            )
        except Exception as e:
            logger.critical("Unhandled exception: %s", str(e), exc_info=1)
            return Response(
                {"error": "DJANGO:Unhandled exception", "data": str(e)}, status=500
            )


class CeleryTaskLogDetails(APIView):
    """
    API endpoint for accessing imapsync logfile contents
    """

    def get(self, request, task_id, log_file):
        logger.debug("Got request for task %s logs", task_id)
        config = settings.PYMAP_SETTINGS
        log_directory = config.get("LOGDIR")
        tail_timeout: int = int(request.GET.get("ttimeout", 5))
        tail_count: int = int(request.GET.get("tcount", 100))
        logger.debug("Full request GET parameters: %s", request.GET)
        # Tail the last X lines from the log file and return it
        try:
            f_path = f"{log_directory}/{task_id}/{log_file}"
            if not isfile(f_path):
                return JsonResponse(
                    {"error": f"DJANGO:File {f_path} was not found"}, status=404
                )
            logger.debug(
                "Tail timeout is: %s\nTail count is: %s", tail_timeout, tail_count
            )

            p1 = Popen(
                ["tail", "-n", str(tail_count), f_path],
                stdout=PIPE,
                stderr=PIPE,
                text=True,
            )
            content, error = p1.communicate(timeout=tail_timeout)
            _status: int = 300 if error else 200
            return JsonResponse({"content": content, "error": error}, status=_status)
        except TimeoutExpired:
            logger.error("Failed to tail the file: %s", f_path, exc_info=1)
            return JsonResponse(
                {
                    "error": f"DJANGO:Could not fetch data",
                    "data": f"Failed to tail the file -> {f_path} after {tail_timeout} seconds",
                },
                status=400,
            )
        except Exception as e:
            logger.critical("Unhandled exception: %s", e.__str__(), exc_info=1)
            return JsonResponse(
                {"error": "DJANGO:Unhandled exception", "data": e.__str__()}, status=400
            )


class CustomLoginView(LoginView):
    template_name = "login.html"
    success_url = "/"
