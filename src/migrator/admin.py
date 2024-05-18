from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ngettext

from .models import CeleryTask

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ["task_id", "source", "destination", "owner", "start_time"]
    ordering = ["-start_time"]
    actions = ["archive_selected"]

    @admin.action(description="Mark selected tasks as archived")
    def archive_selected(self, request, queryset):
        queryset.update(archived=True)
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
