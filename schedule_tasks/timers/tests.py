# Create your tests here.
# timers/tests.py
import time
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponseNotFound
from django.test import TestCase
from django.utils.timezone import now
from rest_framework.test import APIClient

from .models import Timer


class TimerTests(TestCase):
    """
    Test case for the Timer model and its related views.
    """

    def setUp(self) -> None:
        """
        Set up the test client for API requests.
        """
        self.client = APIClient()

    def test_create_timer(self) -> None:
        """
        Tests the creation of a new timer via the API.

        Sends a POST request to create a new timer with the specified duration and URL.
        Asserts that the response status code is 201 (Created) and that the response
        contains the timer ID and the time left until the timer expires.

        Sample Example POST request: http://localhost:8000/timer with following data
        {
        "hours": 0,
        "minutes": 1,
        "seconds": 0,
        "url": "https://webhook.site/c91aafb2-0e75-4cc6-bd1f-bc3888b1f629"
        }
        """
        response = self.client.post(
            "/timer",
            {
                "hours": 0,
                "minutes": 1,
                "seconds": 0,
                "url": "https://example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data)
        self.assertIn("time_left", response.data)
        self.assertTrue(response.data["time_left"] >= 59)
        self.assertTrue(isinstance(str(response.data["id"]), str))

    def test_get_timer(self) -> None:
        """
        Tests the retrieval of an existing timer via the API.

        Creates a timer object and sends a GET request to retrieve the timer.
        Asserts that the response status code is 200 (OK) and that the response
        contains the timer ID and the time left until the timer expires.
        """
        timer = Timer.objects.create(
            url="https://example.com",
            scheduled_time=now() + timedelta(seconds=60),
        )
        response = self.client.get(f"/timer/{timer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.data)
        self.assertIn("time_left", response.data)
        self.assertEqual(str(response.data["id"]), str(timer.id))
        self.assertTrue(response.data["time_left"] >= 59)
        self.assertTrue(isinstance(response.data["time_left"], int))

    def test_create_timer_invalid_data(self) -> None:
        """
        Tests that creating a timer with invalid data results in a 400 response.

        Sends a POST request with invalid data (e.g., negative hours).
        Asserts that the response status code is 400 (Bad Request) and that
        the response contains the appropriate validation errors.
        """
        response = self.client.post(
            "/timer",
            {
                "hours": -1,
                "minutes": 1,
                "seconds": 0,
                "url": "https://example.com",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("hours", response.data)
        self.assertTrue(isinstance(response.data["hours"], list))

    def test_get_nonexistent_timer(self) -> None:
        """
        Tests that retrieving a timer with a non-existent ID results in a 404 response.

        Sends a GET request for a timer with a non-existent ID.
        Asserts that the response status code is 404 (Not Found) and that the response
        is an instance of HttpResponseNotFound.
        """
        response = self.client.get("/timer/nonexistent_id")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(isinstance(response, HttpResponseNotFound))
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

    @patch("timers.models.Timer.objects.get")
    def test_get_validation_error(self, mock_get) -> None:
        """
        Tests handling of validation errors when retrieving a timer.

        Mocks the Timer.objects.get method to raise a DjangoValidationError.
        Sends a GET request for a timer with an invalid ID.
        Asserts that the response status code is 404 (Not Found) and that the response
        content type is "text/html; charset=utf-8".
        """
        mock_get.side_effect = DjangoValidationError("Invalid data")
        response = self.client.get("/timer/invalid_id")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")

    def test_timer_expiry(self) -> None:
        """
        Tests that a timer expires correctly and the time left is zero after the scheduled time passes.

        Creates a timer object with a short duration.
        Sends a GET request to retrieve the timer before and after it expires.
        Asserts that the time left is correctly updated before and after expiry.
        """
        timer = Timer.objects.create(
            url="https://example.com",
            scheduled_time=now() + timedelta(seconds=2),
        )
        response = self.client.get(f"/timer/{timer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            1 <= response.data["time_left"] <= 2
        )  # Acceptable range
        self.assertIn("id", response.data)
        self.assertTrue(isinstance(response.data["time_left"], int))

        # Wait for the timer to expire with a small buffer
        time.sleep(3)

        response = self.client.get(f"/timer/{timer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["time_left"], 0)
