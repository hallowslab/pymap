from django.contrib import admin, messages
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ngettext

from django_celery_results.models import TaskResult

from .models import CeleryTask

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]
    actions = ["archive_selected"]

    @admin.action(description="Archive selected tasks")
    def archive_selected(self, request, queryset) -> None:
        for task in queryset:
            try:
                result = TaskResult.objects.filter(task_id=task.task_id)
                if result.exists():
                    result.delete()
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
