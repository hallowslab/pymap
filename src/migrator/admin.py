from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.utils.translation import ngettext
from celery.result import AsyncResult

from django_celery_results.models import TaskResult

from .models import CeleryTask
from pymap import celery_app

# Register your models here.


class TaskAdmin(ModelAdmin):
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]
    actions = ["archive_selected"]

    @admin.action(description="Archive selected tasks")
    def archive_selected(self, request, queryset) -> None:
        for task in queryset:
            try:
                result = AsyncResult(task.task_id, app=celery_app)
                result.get(timeout=5.0)
                result.forget()
            except TimeoutError:
                self.message_user.error(request, f"Failed to clear results for Task ID: {task.task_id}", messages.WARNING)
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


admin.site.register(CeleryTask, TaskAdmin)
