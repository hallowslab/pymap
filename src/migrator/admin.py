from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.urls import path
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.contrib.auth.models import User, Group
from django.contrib import admin, messages
from django.contrib.admin import AdminSite, ModelAdmin
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ngettext
from celery.result import AsyncResult

from django_celery_results.models import TaskResult, GroupResult
from django_celery_beat.models import SolarSchedule, IntervalSchedule, ClockedSchedule, CrontabSchedule, PeriodicTask

from .models import CeleryTask
from .tasks import purge_results, validate_finished
from pymap import celery_app

# Register your models here.


class TaskAdmin(ModelAdmin):
    actions = ["purge_results", "validate_finished", "archive_selected"]
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]

    @admin.action(description="Archive selected tasks")
    def archive_selected(self, request, queryset) -> None:
        for task in queryset:
            try:
                result = AsyncResult(task.task_id, app=celery_app)
                result.get(timeout=5.0)
                result.forget()
            except TimeoutError:
                self.message_user(
                    request,
                    f"Failed to clear results for Task ID: {task.task_id}",
                    messages.WARNING,
                )
            try:
                result = TaskResult.objects.get(task_id=task.task_id)
                result.delete()
            except ObjectDoesNotExist:
                self.message_user(
                    request,
                    f"The result does not seem to exist in our database: {task.task_id}",
                    messages.WARNING,
                )
                continue  # Continue to the next task
            except ImproperlyConfigured:
                # If TaskResult model is not available, log or handle the situation
                self.message_user(
                    request,
                    "Task results backend is not configured to use django-db.",
                    messages.WARNING,
                )
                break  # Exit the loop if the backend is not configured
            except Exception as e:
                # Handle other exceptions
                self.message_user(
                    request,
                    f"An error occurred while deleting task results: {e}",
                    messages.ERROR,
                )
                continue  # Continue to the next task

        # Update the queryset to mark tasks as archived
        updated = queryset.update(archived=True)
        self.message_user(
            request,
            ngettext(
                "%d task was successfully marked as archived.",
                "%d Tasks were successfully marked as archived.",
                updated,
            )
            % updated,
            messages.SUCCESS,
        )



    @admin.action(description="Sets finished to true on tasks that may have crashed")
    def admin_validate_finished(self, request, _) -> None:
        validate_finished.delay()
        self.message_user(
            request, "Task validate_finished dispatched to worker", messages.SUCCESS
        )

    @admin.action(description="Purges Task results from database")
    def admin_purge_results(self, request, _) -> None:
        purge_results.delay(1,0,0,finished=True)
        self.message_user(
            request, "Task purge_results dispatched to worker", messages.SUCCESS
        )


class CustomAdminSite(AdminSite):
    site_title: str = "Pymap site admin"
    site_header: str = "Pymap administration"
    index_title: str = "Pymap administration"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("run-task/", self.admin_view(self.task_view), name="run-task"),
        ]
        return custom_urls + urls

    def task_view(
        self, request
    ) -> (TemplateResponse | HttpResponseRedirect | HttpResponsePermanentRedirect):
        if request.method == "POST":
            if "purge_results" in request.POST:
                purge_results.delay()
            elif "validate_finished" in request.POST:
                validate_finished.delay()
            return redirect("..")
        context = dict(
            self.each_context(request),
        )
        return TemplateResponse(request, "admin/run_task.html", context)

custom_admin_site = CustomAdminSite(name="custom_admin")
# Custom task management model
custom_admin_site.register(CeleryTask, TaskAdmin)
# Django models
custom_admin_site.register((User,Group))
# Celery results
custom_admin_site.register((TaskResult,GroupResult))
# Periodic tasks
custom_admin_site.register((SolarSchedule,IntervalSchedule,ClockedSchedule,CrontabSchedule,PeriodicTask))