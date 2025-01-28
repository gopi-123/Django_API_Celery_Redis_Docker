# timers/urls.py
from django.urls import path

from . import views  # Ensure this import is present

urlpatterns = [
    path("ui_timer", views.test_timer_form, name="test_timer_form"),
    path("timer", views.TimerView.as_view(), name="create_timer"),
    path(
        "timer/<uuid:timer_id>",
        views.TimerDetailView.as_view(),
        name="timer_detail",
    ),
]
