from django.urls import path, register_converter
from django.contrib.auth.decorators import login_required

from . import views

from .converters import LogfileConverter

register_converter(LogfileConverter, "log")

app_name="migrator"

urlpatterns = [
    path("", login_required(views.index), name="index"),
    path("sync/", login_required(views.sync), name="sync"),
    path("tasks/", login_required(views.tasks), name="tasks"),
    path("tasks/<str:task_id>/", login_required(views.task_details), name="task-id"),
    path(
        "tasks/<str:task_id>/<log:log_file>/",
        login_required(views.log_details),
        name="task-log",
    ),
    path(
        "tasks/<str:task_id>/<log:log_file>/download/",
        login_required(views.DownloadLog.as_view()),
        name="task-log-download",
    ),
    path(
        "api/tasks/list/",
        login_required(views.CeleryTaskList.as_view()),
        name="tasks-list",
    ),
    path(
        "api/tasks/archive/",
        login_required(views.ArchiveTask.as_view()),
        name="tasks-archive",
    ),
    path(
        "api/tasks/<str:task_id>/",
        login_required(views.CeleryTaskDetails.as_view()),
        name="tasks-details",
    ),
    path(
        "api/tasks/<str:task_id>/<log:log_file>/",
        login_required(views.CeleryTaskLogDetails.as_view()),
        name="tasks-log-details",
    ),
]
