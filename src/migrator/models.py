# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class TaskStatistics(models.Model):
    total_task_count = models.IntegerField(default=0)
    total_run_time = models.IntegerField(default=0)

    def __str__(self):
        return f"Global Task Statistics"


class CeleryTask(models.Model):
    """
        Model for an individual task
    """
    id = models.AutoField(primary_key=True)
    task_id = models.CharField(max_length=255)  # Adjust the max_length as needed
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    log_path = models.CharField(max_length=255)  # Adjust the max_length as needed
    n_accounts = models.IntegerField()
    domains = models.CharField(max_length=100, null=True, blank=True)
    archived = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True, blank=True)
    # end_time = models.DateTimeField(default=0,blank=True)
    run_time = models.IntegerField(default=0)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # Assuming User is the Django User model

    def __str__(self):
        return (
            f"<ID:{self.id} | TID:{self.task_id}><{self.source} | {self.destination}>"
        )
