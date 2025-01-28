# timers/tasks.py
from __future__ import absolute_import, unicode_literals

import logging

import requests
from celery import shared_task
from django.utils import timezone

from .models import Timer

logger = logging.getLogger(__name__)


# The shared_task decorator makes the function available as a Celery task
@shared_task
def fire_webhook(timer_id: str) -> None:
    """
    Fire the webhook for a given timer.

    Retrieves the Timer object with the given timer_id and ensures it hasn't been fired (is_fired=False).
    Sends a POST request to the specified URL with the timer ID in the payload (data in JSON format).
    After sending the POST request, the Timer object is updated to mark it as "fired" and saved back to the database.
    i.e Marks the timer as fired (is_fired=True) and saves the changes.
    catching the Timer.DoesNotExist exception is to ensure that  function doesn't crash if the timer ID doesn't correspond to an existing timer
    Handles the case where the Timer object does not exist (by using the try and except block.)

    Args:
        timer_id (str): The unique identifier of the timer to be fired.

    Raises:
        Timer.DoesNotExist: If the timer with the given ID does not exist or has already been fired.
        requests.RequestException: If the POST request to the URL fails.

    Returns:
        None
    """
    logger.info(f"Attempting to fire webhook for timer ID: {timer_id}")
    try:
        timer = Timer.objects.get(id=timer_id, is_fired=False)
        logger.info(f"Timer found: {timer.id}, URL: {timer.url}")

        # Sends a POST request to the specified URL with the timer.id in the payload as a JSON object
        response = requests.post(timer.url, json={"id": str(timer.id)})
        response.raise_for_status()
        logger.info(
            f"Webhook triggered successfully for timer ID: {timer.id}, Response status: {response.status_code}"
        )

        # Mark the timer as fired and save changes
        timer.is_fired = True
        timer.save()
        logger.info(f"Timer marked as fired: {timer.id}")
    except Timer.DoesNotExist:
        logger.error(
            f"Timer with ID {timer_id} does not exist or is already fired."
        )
    except requests.RequestException as e:
        logger.error(
            f"Failed to trigger webhook for timer ID: {timer_id}. Error: {e}"
        )


@shared_task
def check_expired_timers() -> None:
    """
    Check for and handle expired timers.

    Retrieves all Timer objects that have not been fired and are past their scheduled time.
    Fires the webhook for each expired timer by calling the fire_webhook task.

    Raises:
        Timer.DoesNotExist: If no expired timers are found.

    Returns:
        None
    """
    logger.info("## Executing check_expired_timers task.")
    expired_timers = Timer.objects.filter(
        is_fired=False, scheduled_time__lt=timezone.now()
    )

    logger.info(f"++ Expired_timers list:{expired_timers}")
    for timer in expired_timers:
        logger.info(f" ** timer value in expired_timers_list:{timer}")
        fire_webhook.delay(timer.id)
    logger.info("** Completed check_expired_timers task.")
