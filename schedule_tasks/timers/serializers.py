# timers/serializers.py
# Serializer for Validations, This will handle user input validation, including invalid inputs.
from datetime import datetime, timedelta, timezone

from rest_framework import serializers

from .models import Timer


class TimerSerializer(serializers.ModelSerializer):
    """
    Serializer for Timer model, handling user input validation, including invalid inputs.

    Serializer Fields:
        hours (int): Number of hours for the timer (write-only).
        minutes (int): Number of minutes for the timer (write-only).
        seconds (int): Number of seconds for the timer (write-only).
    """

    hours = serializers.IntegerField(
        write_only=True, min_value=0, required=True
    )
    minutes = serializers.IntegerField(
        write_only=True, min_value=0, required=True
    )
    seconds = serializers.IntegerField(
        write_only=True, min_value=0, required=True
    )

    class Meta:
        """
        Meta class defines the model to serialize and the fields to include.
        Ensures that scheduled_time is calculated internally and isn't required in the input JSON.
        """

        model = Timer
        fields = [
            "id",
            "url",
            "scheduled_time",
            "is_fired",
            "hours",
            "minutes",
            "seconds",
        ]
        # Following Fucntionality  changes ensure that scheduled_time is calculated internally and isn't required in the input JSON.
        read_only_fields = ["id", "scheduled_time", "is_fired"]

    def validate(self, data: dict) -> dict:
        """
        Ensures that the timer duration cannot be zero.

        Args:
            data (dict): The validated data containing hours, minutes, and seconds.

        Raises:
            serializers.ValidationError: If the timer duration is zero.

        Returns:
            dict: The validated data.
        """

        if (
            data["hours"] == 0
            and data["minutes"] == 0
            and data["seconds"] == 0
        ):
            raise serializers.ValidationError("Timer duration cannot be zero.")
        return data

    def create(self, validated_data: dict) -> Timer:
        """
        Calculates the total delay in seconds and sets the scheduled_time based on the current time plus the delay.
        timezone.utc ensures the current time is in the UTC (Coordinated Universal Time) timezone, which is a standardized time reference that avoids timezone-related issues.
        timedelta represents the duration to be added to the current time, The timedelta class from the datetime module, creates a duration object representing the total number of seconds calculated from the input hours, minutes, and seconds.

        Args:
            validated_data (dict): The validated data containing hours, minutes, and seconds.

        Returns:
            Timer: The created Timer instance.
        """
        total_seconds = (
            validated_data.pop("hours") * 3600
            + validated_data.pop("minutes") * 60
            + validated_data.pop("seconds")
        )
        validated_data["scheduled_time"] = datetime.now(
            timezone.utc
        ) + timedelta(seconds=total_seconds)
        return Timer.objects.create(**validated_data)
