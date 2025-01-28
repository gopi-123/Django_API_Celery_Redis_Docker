# Create your views here.
# timers/views.py
# Import necessary modules and classes from Django REST framework, Django models, serializers, timezone utilities, and Celery tasks.
import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.timezone import now
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Timer
from .serializers import TimerSerializer
from .tasks import fire_webhook

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimerView(APIView):
    """
    Handles the creation of timers and scheduling with Celery.
    Validates the incoming request data using TimerSerializer.
    Saves the timer object and schedules the webhook firing using Celery.

    Implements a “set timer” endpoint: /timer
    - Receives a JSON object containing hours, minutes, seconds, and a web url.
    - Returns a JSON object with the amount of seconds left until the timer expires
      and an id for querying the timer in the future.
    - The endpoint starts an internal timer, which fires a webhook to the
      defined URL when the timer expires.
    """

    def post(self, request: Request) -> Response:
        """
        Handles the creation of a timer.
        Implements a “set timer” endpoint: /timer

        Uses TimerSerializer to validate and save the timer data.

        Args:
            request: The HTTP request object containing the timer data.

        Returns:
            Response: A JSON response containing the id of the created timer and
                      the amount of time left until the timer expires. If the request
                      data is invalid, returns a JSON response containing the errors.

        Sample Example:
          POST request: http://localhost:8000/timer with following data
            {
            "hours": 0,
            "minutes": 1,
            "seconds": 0,
            "url": "https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629"
            }

        Expected Sample Response:
            {
            "id": "766cb2bb-5854-4b39-aea6-7343e9916b13",
            "time_left": 59
            }

        """
        serializer = TimerSerializer(data=request.data)
        if serializer.is_valid():
            timer = serializer.save()
            # Using assert isinstance for runtime checking
            assert isinstance(timer, Timer), "Expected a Timer instance"
            self.schedule_webhook(timer)

            # Calculate the time left until the scheduled_time by subtracting the current time (now()) from the scheduled_time. Use max() to ensure the time left is not negative.
            time_left = (
                int(max((timer.scheduled_time - now()).total_seconds(), 0))
                if not timer.is_fired
                else 0
            )
            logger.info(
                f"timer:{timer} \nSerializer:{serializer} \n data:{request.data} \n time_left:{time_left}"
            )
            return Response(
                {"id": timer.id, "time_left": time_left},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def schedule_webhook(self, timer: Timer) -> None:
        """
        Schedules the webhook firing using Celery.

        Calculates the delay in seconds from the current time to the scheduled time
        and schedules the webhook firing using Celery.

        Args:
            timer: The timer object containing the scheduled time and other relevant information.

        Returns:
            None
        """
        delay = max((timer.scheduled_time - now()).total_seconds(), 0)
        fire_webhook.apply_async((str(timer.id),), countdown=delay)


class TimerDetailView(APIView):
    """
    Handles querying a timer's status.
    Retrieves the timer object by ID and returns the time left until it fires, along with its fired status.

    Implement a “get timer” endpoint: /timer/{timer_uuid}

    - Receives the timer id in the URL, as the resource uuid.
    - Returns a JSON object with the amount of seconds left until the timer expires.
    - If the timer already expired, returns 0.
    """

    def get(self, request: Request, timer_id: str) -> Response:
        """
        Retrieves the timer by its ID.
        Implement a “get timer” endpoint: /timer/{timer_uuid}

        Calculates the time left until the timer fires (if it hasn't already fired).

        Args:
            request: Request, timer_id: str) -> Response:
            timer_id: The ID of the timer to be retrieved.

        Returns:
            Response: A JSON response containing the timer's ID, time left, and fired status.
                      If the timer is not found, returns a JSON response with an error message and status 404.
                      If there is a validation error, returns a JSON response with the error message and status 400.


        Sample Example: GET request: http://localhost:8000/timer/766cb2bb-5854-4b39-aea6-7343e9916b13

        Sample response:
                      {
                        "id": "766cb2bb-5854-4b39-aea6-7343e9916b13",
                        "time_left": 0
                        }

        """

        try:
            logger.info(
                f"#### timer_id:{timer_id}, type_timer_id:{type(timer_id)}"
            )
            timer = Timer.objects.get(id=timer_id)
            logger.info(f"## GET timer:{timer}")
            time_left = (
                int(max((timer.scheduled_time - now()).total_seconds(), 0))
                if not timer.is_fired
                else 0
            )
            return Response({"id": timer.id, "time_left": time_left})
        except Timer.DoesNotExist:
            return Response({"error": "Timer not found"}, status=404)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)


# Testing purpose
def test_timer_form(request: HttpRequest) -> HttpResponse:
    """
    Render the test timer form HTML template.

    This view function handles the rendering of the test_timer_form.html template,
    which provides a form for creating timers. It is primarily used for testing
    purposes to manually create timers via a web interface.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered test_timer_form.html template.
    """
    return render(request, "test_timer_form.html")
