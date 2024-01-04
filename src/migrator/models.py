# Create your models here.
from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=60, unique=True)
    email = models.EmailField(unique=True, max_length=200)
    password = models.TextField()
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username


class CeleryTask(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    log_path = models.CharField(max_length=255)  # Adjust the max_length as needed
    task_id = models.CharField(max_length=255)  # Adjust the max_length as needed
    n_accounts = models.IntegerField()
    domains = models.CharField(max_length=100, null=True, blank=True)
    archived = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    run_time = models.IntegerField()
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE
    )  # Assuming User is the Django User model

    def serialize(self):
        return {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
            if field.name != "id"
        }

    def __str__(self):
        return (
            f"<ID:{self.id} | TID:{self.task_id}><{self.source} | {self.destination}>"
        )
