from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path("", login_required(views.index), name="index"),
    path("tasks/", login_required(views.tasks), name="tasks"),
    path("sync/", login_required(views.sync), name="sync"),
    path(
        "api/tasks-list",
        login_required(views.CeleryTaskList.as_view()),
        name="tasks-list",
    ),
    path(
        "api/tasks-detail",
        login_required(views.CeleryTaskDetail.as_view()),
        name="tasks-detail",
    ),
    path("login/", views.CustomLoginView.as_view(), name="login"),
]
