from rest_framework import serializers
from .models import Habit


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = [
            "id", "user", "action", "time_of_day", "location",
            "is_pleasant", "reward", "related_habit",
            "periodicity_days", "execution_time_seconds", "is_public",
            "created_at", "updated_at"
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
