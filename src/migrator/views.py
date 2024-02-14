# Create your views here.
import logging
import json
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
from .serializers import CeleryTaskSerializer, TaskIdListSerializer
from .forms import SyncForm, CustomUserChangeForm
from .tasks import call_system
from .utilites.helpers import get_logs_status
from core.pymap_core import ScriptGenerator

logger = logging.getLogger(__name__)


# IMPORTANT: All these views should be in the migrator: namespace


def index(request):
    return render(request, "home.html", {})


def user_account(request):
    user = request.user
    return render(request, "account.html", {"user": user})


def update_account(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(
                "migrator:user-account"
            )  # Redirect to user's account page after successful update
    else:
        form = CustomUserChangeForm(instance=request.user)
    user = request.user
    return render(
        request, "update_account.html", {"form": form, "username": user.username}
    )


def tasks(request):
    """
    Renders task list template
    """
    return render(request, "tasks.html", {})


def task_details(request, task_id):
    """
    Renders task list details from the provided task_id
    """
    return render(request, "task_details.html", {"task_id": task_id})


def log_details(request, task_id, log_file):
    """
    Renders individual log details template from task_id and log_file
    """
    return render(
        request, "log_details.html", {"task_id": task_id, "log_file": log_file}
    )


def sync(request):
    """
    Endpoint for requesting a sync, creates a new task and signals the worker
    """
    if request.method == "POST":
        form = SyncForm(request.POST)
        # logger.debug("POST data: %s", request.POST)
        if not form.is_valid():
            logger.error("Form errors: %s", form.errors)
        else:
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

            target_url = reverse("migrator:tasks")
            return redirect(target_url)
    else:
        form = SyncForm()

    return render(request, "sync.html", {"form": form})


## CLASSES
class DownloadLog(View):
    """
    Given a task id downloads to the user's browser the requested log file
    """

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
        order = request.GET.get("order", [])
        columns = request.GET.get("columns", [])
        print("GET", request.GET)

        # Parsing the order parameter
        order_str = request.GET.get("order", "")
        print("ORDER_STR", order_str)
        order = json.loads(order_str) if order_str else []

        # Parsing the columns parameter
        columns_str = request.GET.get("columns", "")
        print("COLUMNS_STR", columns_str)
        columns = json.loads(columns_str) if columns_str else []

        # Now you can access information in the order and columns arrays
        for column in columns:
            # Access individual column properties
            print(column)

        # Access information in the order array
        for order_item in order:
            print(order_item)

        # Filtering based on search value
        queryset = self.filter_queryset(self.get_queryset())
        if search_value != "":
            queryset = queryset.filter(source__icontains=search_value)
            # queryset.order_by(search_value)

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


class ArchiveTask(APIView):
    """
    API endpoint for setting a task as archived
    """

    def post(self, request, *args, **kwargs):
        serializer = TaskIdListSerializer(data=request.data)

        if serializer.is_valid():
            task_ids = serializer.validated_data["task_ids"]

            # Check ownership for each task ID
            user = self.request.user  # Assuming the user is authenticated
            owned_task_ids = CeleryTask.objects.filter(
                user=user, id__in=task_ids
            ).values_list("id", flat=True)

            # Perform actions based on ownership
            for task_id in task_ids:
                if task_id in owned_task_ids:
                    # User owns this task, perform your logic here
                    print(f"User owns task with ID {task_id}")
                    print(f"Task {owned_task_ids[task_id]}")
                else:
                    # User does not own this task, handle accordingly
                    print(f"User does not own task with ID {task_id}")
            return Response(
                {"message": "Ownership verification successful"}, status=200
            )
        return Response(serializer.errors, status=400)


class CancelTask(APIView):
    """
    API endpoint to stop a task execution or cancel it's scheduling
    """

    def post(self, request, *args, **kwargs):
        serializer = TaskIdListSerializer(data=request.data)
        if serializer.is_valid():
            task_ids = serializer.validated_data["task_ids"]

            user = self.request.user
            # owned_tasks
            return Response(
                {"message": "Ownership verification successful"}, status=200
            )
        return Response(serializer.errors, status=400)
