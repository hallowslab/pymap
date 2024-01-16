from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CeleryTask


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class CeleryTaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer()  # Use the UserSerializer for the owner field

    class Meta:
        model = CeleryTask
        fields = [
            "id",
            "task_id",
            "source",
            "destination",
            "log_path",
            "n_accounts",
            "domains",
            "archived",
            "finished",
            "start_time",
            "run_time",
            "owner",
        ]
