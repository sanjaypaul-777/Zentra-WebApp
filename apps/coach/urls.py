from django.urls import path

from . import views

app_name = "coach"

urlpatterns = [
    # Merchant chat API — /dashboard/coach/api/...
    path("coach/api/session/", views.api_session, name="api_session"),
    path("coach/api/send/", views.api_send, name="api_send"),
    path("coach/api/request-coach/", views.api_request_coach, name="api_request_coach"),
    path("coach/api/close/", views.api_close, name="api_close"),
    path("coach/api/me/", views.api_coach_check, name="api_me"),
    # Coach desk — /dashboard/coach-desk/
    path("coach-desk/", views.coach_desk_page, name="desk"),
    path("coach-desk/api/state/", views.api_desk_state, name="desk_state"),
    path(
        "coach-desk/api/sessions/<int:session_id>/",
        views.api_desk_session_messages,
        name="desk_session",
    ),
    path(
        "coach-desk/api/sessions/<int:session_id>/claim/",
        views.api_desk_claim,
        name="desk_claim",
    ),
    path(
        "coach-desk/api/sessions/<int:session_id>/reassign/",
        views.api_desk_reassign,
        name="desk_reassign",
    ),
    path(
        "coach-desk/api/sessions/<int:session_id>/leave/",
        views.api_desk_leave,
        name="desk_leave",
    ),
    path(
        "coach-desk/api/sessions/<int:session_id>/close/",
        views.api_desk_close,
        name="desk_close",
    ),
    path(
        "coach-desk/api/sessions/<int:session_id>/send/",
        views.api_desk_send,
        name="desk_send",
    ),
    path("coach-desk/api/presence/", views.api_desk_presence, name="desk_presence"),
]
