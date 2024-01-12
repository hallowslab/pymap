from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path("", login_required(views.index), name="index"),
    path("tasks/", login_required(views.tasks), name="tasks"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
]
