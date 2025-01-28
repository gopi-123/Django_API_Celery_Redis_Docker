# Create your models here.
# timers/models.py
import uuid

from django.db import models


class Timer(models.Model):
    """
    Timer model representing a scheduled event with a webhook.

    Attributes:
        id (UUID): The unique identifier of the timer (refers to the id attribute of the Timer instance).
        url (str): The URL to be called when the timer fires.
        scheduled_time (datetime): The time when the timer is scheduled to fire.
        is_fired (bool): Indicates whether the timer's webhook has been fired.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    scheduled_time = models.DateTimeField()
    is_fired = models.BooleanField(default=False)

    def __str__(self) -> str:
        """
        Returns a string representation of the Timer instance.

        Example: "Timer_id 12345-67890 - Fired_status: True
        Example: " Assuming you have a Timer object with id=12345-67890 and is_fired=True, calling str(time_instance) will return Timer 12345-67890 - Fired: True"
        """
        return f"Timer_id {self.id} - Fired_status: {self.is_fired}"
