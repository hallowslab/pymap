from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CeleryTask


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class CeleryTaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer()  # UserSerializer required for the owner field

    class Meta:
        model = CeleryTask
        fields = "__all__"

class TaskIdListSerializer(serializers.Serializer):
    task_ids = serializers.ListField(child=serializers.CharField())