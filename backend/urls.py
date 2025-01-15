from django.urls import path

from backend.views import ping_view, user_list

urlpatterns = [
    path("v1/ping/", ping_view, name="ping_view"),
    path("v1/users/", user_list, name="user_list"),
]