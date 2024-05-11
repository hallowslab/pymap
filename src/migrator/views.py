# Create your views here.
import logging
import json
from subprocess import PIPE, Popen, TimeoutExpired
from typing import List, Optional
from os import listdir
from os.path import isfile, join, exists
from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.request import Request as APIRequest
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response as APIResponse
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView

from .models import CeleryTask
from .serializers import CeleryTaskSerializer, TaskIdListSerializer
from .forms import SyncForm, CustomUserChangeForm
from .tasks import call_system
from pymap import celery_app
from .utilites.helpers import get_logs_status
from core.pymap_core import ScriptGenerator

logger = logging.getLogger(__name__)


# IMPORTANT: All these views should be in the migrator: namespace


@login_required
def index(request: HttpRequest) -> HttpResponse:
    total_tasks = CeleryTask.objects.count()
    total_run_time = CeleryTask.objects.aggregate(Sum("run_time"))["run_time__sum"]
    total_n_accounts = CeleryTask.objects.aggregate(Sum("n_accounts"))[
        "n_accounts__sum"
    ]
    active_users_count = User.objects.filter(is_active=True).count()
    staff_count = User.objects.filter(is_active=True, is_staff=True).count()

    context = {
        "total_tasks": total_tasks,
        "total_run_time": total_run_time,
        "total_n_accounts": total_n_accounts,
        "active_users_count": active_users_count,
        "staff_count": staff_count,
    }
    return render(request, "home.html", context)


@login_required
def user_account(request: HttpRequest) -> HttpResponse:
    user = request.user
    return render(request, "account.html", {"user": user})


@login_required
def update_account(
    request: HttpRequest,
) -> (HttpResponse | HttpResponseRedirect):
    assert isinstance(request.user, User)  # AbstractBaseUser has no .username
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(
                "migrator:user-account", permanent=False
            )  # Redirect to user's account page after successful update
    else:
        form = CustomUserChangeForm(instance=request.user)
    username = request.user.username
    return render(request, "update_account.html", {"form": form, "username": username})


@login_required
def tasks(request: HttpRequest) -> HttpResponse:
    """
    Renders task list template
    """
    return render(request, "tasks.html", {})


@login_required
def task_details(request: HttpRequest, task_id: str) -> HttpResponse:
    """
    Renders task list details from the provided task_id
    """
    return render(request, "task_details.html", {"task_id": task_id})


@login_required
def log_details(request: HttpRequest, task_id: str, log_file: str) -> HttpResponse:
    """
    Renders individual log details template from task_id and log_file
    """
    return render(
        request, "log_details.html", {"task_id": task_id, "log_file": log_file}
    )


@login_required
def sync(request: HttpRequest) -> (HttpResponse | HttpResponseRedirect):
    """
    Endpoint for requesting a sync, creates a new task and signals the worker
    """
    assert isinstance(request.user, User)  # AbstractBaseUser has no .username
    if request.method == "POST":
        form = SyncForm(request.POST)
        # logger.debug("POST data: %s", request.POST)
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
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
                f"USER: {user.username} requested a sync for {source} -> {destination}"
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
                pymap_logdir=settings.PYMAP_LOGDIR,
            )
            content = gen.process_strings(input_text)

            # TODO: Strip out passwords before logging commands
            # logger.debug(
            #     "Received the following output from generator:\n %s", content
            # )

            task = call_system.delay(content)
            logger.info(
                f"Starting background task with ID: {task.id} from User: {user.username}"
            )

            # Don't forget to save the task id and respective inputs to the database
            root_log_directory = settings.PYMAP_LOGDIR
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
            return redirect(target_url, permanent=False)
    else:
        form = SyncForm()

    return render(request, "sync.html", {"form": form})


@login_required
def download_log(request: HttpRequest, task_id: str, log_file: str) -> HttpResponse:
    logger.debug(f"Got request for a download for: {task_id}/{log_file}")
    log_directory: Optional[str] = settings.PYMAP_LOGDIR
    if log_directory:
        log_path = join(log_directory, task_id, log_file)
        if exists(log_path):
            with open(log_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="application/text")
                response["Content-Disposition"] = f'attachment; filename="{log_file}"'
            return response
    return HttpResponse("Log file not found.", status=404)


## CLASSES
class CeleryTaskList(ListCreateAPIView):
    """
    API endpoint to fetch all tasks
    """

    permission_classes = [IsAuthenticated]
    # Here we obtain a queryset from the model itself
    queryset = CeleryTask.objects.all()
    serializer_class = CeleryTaskSerializer

    def _get_user_queryset(self) -> None:
        pass

    def list(self, request: APIRequest, *args: object, **kwargs: object) -> APIResponse:
        # Handle DataTables parameters
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")
        logger.debug("GET", request.GET)

        # Parsing the order parameter
        order_str = request.GET.get("order", "")
        logger.debug("ORDER_STR: %s", order_str)
        order = json.loads(order_str) if order_str else []

        # Parsing the columns parameter
        columns_str = request.GET.get("columns", "")
        logger.debug("COLUMNS_STR: %s", columns_str)
        columns = json.loads(columns_str) if columns_str else []

        # Now you can access information in the order and columns arrays
        # for column in columns:
        #     # Access individual column properties
        #     logger.debug(column)

        # # Access information in the order array
        # for order_item in order:
        #     logger.debug(order_item)

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

        return APIResponse(response_data, status=200)


class CeleryTaskDetails(APIView):
    """
    API endpoint to fetch all jobs inside a task
    """

    permission_classes = [IsAuthenticated]

    def get(
        self, request: APIRequest, task_id: str, format: Optional[str] = None
    ) -> JsonResponse:
        config = settings.PYMAP_SETTINGS
        log_directory: Optional[str] = settings.PYMAP_LOGDIR
        all_logs = []

        try:
            if not log_directory:
                raise FileNotFoundError("")
            # Handle DataTables parameters
            draw = int(request.GET.get("draw", 1))
            start = int(request.GET.get("start", 0))
            length = int(request.GET.get("length", 10))
            search_value = request.GET.get("search[value]", "")

            # Since this data does not get stored we need to generate it
            # TODO: MEMOIZE OR CACHE THIS
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

            return JsonResponse(
                {
                    "draw": draw,
                    "recordsTotal": total_records,
                    "recordsFiltered": total_records,
                    "data": paginated_logs,
                },
                status=200,
            )

        except ValidationError:
            return JsonResponse(
                {"error": "DJANGO:Failed to serialize data", "data": all_logs},
                status=500,
            )
        except FileNotFoundError:
            logger.error(
                f"DJANGO:The log directory: {log_directory} does not exist or was not obtained"
            )
            return JsonResponse(
                {
                    "error": "DJANGO:The directory does not exist on the system",
                    "data": log_directory,
                },
                status=404,
            )
        except Exception as e:
            logger.critical("Unhandled exception: %s", str(e), exc_info=True)
            return JsonResponse(
                {"error": "DJANGO:Unhandled exception", "data": str(e)}, status=500
            )


class CeleryTaskLogDetails(APIView):
    """
    API endpoint for accessing imapsync logfile contents
    """

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request: APIRequest,
        task_id: str,
        log_file: str,
        format: Optional[str] = None,
    ) -> JsonResponse:
        logger.debug(f"Got request for task {task_id} logs")
        config = settings.PYMAP_SETTINGS
        log_directory = settings.PYMAP_LOGDIR
        tail_timeout: int = int(request.GET.get("ttimeout", 5))
        tail_count: int = int(request.GET.get("tcount", 100))
        logger.debug(f"Full request GET parameters: {request.GET}")
        # Tail the last X lines from the log file and return it
        f_path = f"{log_directory}/{task_id}/{log_file}"
        try:
            if not isfile(f_path):
                return JsonResponse(
                    {"error": f"DJANGO:File {f_path} was not found"}, status=404
                )
            logger.debug(
                f"Tail timeout is: {tail_timeout}\nTail count is: {tail_count}"
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
            logger.error(f"Failed to tail the file: {f_path}", exc_info=True)
            return JsonResponse(
                {
                    "error": f"DJANGO:Could not fetch data",
                    "data": f"Failed to tail the file -> {f_path} after {tail_timeout} seconds",
                },
                status=400,
            )
        except Exception as e:
            logger.critical("Unhandled exception: %s", e.__str__(), exc_info=True)
            return JsonResponse(
                {"error": "DJANGO:Unhandled exception", "data": e.__str__()}, status=400
            )


class ArchiveTask(APIView):
    """
    API endpoint for setting a task as archived
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: APIRequest, format: Optional[str] = None) -> JsonResponse:
        # Required User so we can validate the lookup on owned tasks
        # Incompatible type for lookup 'owner': AnonymousUser
        assert isinstance(request.user, SimpleLazyObject)
        # .user .DATA .auth
        # print(request.user)
        # print(type(request.user))
        # print(dir(request.user))
        # print("DATA",request.data)
        serializer = TaskIdListSerializer(data=request.data)
        if serializer.is_valid():
            received_task_ids = serializer.validated_data["task_ids"]

            user = request.user
            tasks = CeleryTask.objects.filter(task_id__in=received_task_ids)
            changes = {}
            logger.info(
                f"User {user} requested archival of the following tasks: {tasks}"
            )
            # Check ownership for each task ID
            for task in tasks:
                # Perform actions based on ownership
                if user.is_superuser or task.owner.id == user.id:
                    logger.debug(
                        f"User {user.username} archived task with ID {task.task_id}"
                    )
                    task.archived = True
                    task.save()
                    changes[task.task_id] = True
                else:
                    logger.debug(
                        f"User {user.username} does not own task with ID {task.task_id}"
                    )
                    changes[task.task_id] = False
            return JsonResponse(
                {"message": "Request accepted", "tasks": changes}, status=200
            )
        logger.error(
            f"Invalid request for user {request.user} reason was :{serializer.errors}",
            request.user,
            serializer.errors,
        )
        return JsonResponse({"errors": serializer.errors}, status=400)


class CancelTask(APIView):
    """
    API endpoint for canceling a scheduled or running task
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: APIRequest, format: Optional[str] = None) -> JsonResponse:
        # Required User so we can validate the lookup on owned tasks
        # Incompatible type for lookup 'owner': AnonymousUser
        assert isinstance(request.user, SimpleLazyObject)
        serializer = TaskIdListSerializer(data=request.data)
        if serializer.is_valid():
            received_task_ids = serializer.validated_data["task_ids"]

            user = request.user
            owner = User.objects.get(id=str(user.id))
            tasks = CeleryTask.objects.filter(task_id__in=received_task_ids)
            changes = {}
            logger.info(
                f"User {user} requested cancellation of the following tasks: {tasks}"
            )
            # Check ownership for each task ID
            for task in tasks:
                # Perform actions based on ownership
                if user.is_superuser or owner.id == user.id:
                    logger.debug(
                        f"User {user.username} cancelled task with ID {task.task_id}"
                    )
                    celery_app.control.revoke(task.task_id, terminate=True)
                    changes[task.task_id] = True
                else:
                    logger.debug(
                        f"User {user.username} does not own task with ID {task.task_id}"
                    )
                    changes[task.task_id] = False
            return JsonResponse(
                {"message": "Request accepted", "tasks": changes}, status=200
            )
        logger.error(
            f"Invalid request for user {request.user} reason was :{serializer.errors}"
        )
        return JsonResponse({"errors": serializer.errors}, status=400)


class DeleteTask(APIView):
    """
    API endpoint for deleting a task and respective log files
    """

    permission_classes = [IsAdminUser]

    def post(self, request: APIRequest, format: Optional[str] = None) -> JsonResponse:
        # Required User so we can validate the lookup on owned tasks
        # Incompatible type for lookup 'owner': AnonymousUser
        assert isinstance(request.user, SimpleLazyObject)
        serializer = TaskIdListSerializer(data=request.data)
        if serializer.is_valid():
            received_task_ids = serializer.validated_data["task_ids"]

            user = request.user
            tasks = CeleryTask.objects.filter(task_id__in=received_task_ids)
            changes = {}
            logger.info(
                f"User {user} requested deletion of the following tasks: {tasks}"
            )
            # Check ownership for each task ID
            for task in tasks:
                # Perform actions based on ownership
                # TODO: Add another group to allow others besides admins to delete tasks
                if user.is_superuser:
                    # Preserve the ID before deletion
                    task_id = task.task_id
                    logger.debug(f"User {user.username} deleted task with ID {task_id}")
                    task.delete()
                    changes[task_id] = True
                else:
                    logger.debug(
                        f"User {user.username} does not own task with ID {task.task_id}"
                    )
                    changes[task.task_id] = False
            return JsonResponse(
                {"message": "Request accepted", "tasks": changes}, status=200
            )
        logger.error(
            "Invalid request for user %s reason was :%s",
            request.user,
            serializer.errors,
        )
        return JsonResponse({"errors": serializer.errors}, status=400)
