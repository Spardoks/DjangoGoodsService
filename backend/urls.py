from django.urls import path

from backend.views import ping_view, user_list, update_shop

urlpatterns = [
    path("v1/ping/", ping_view, name="ping_view"),
    path("v1/users/", user_list, name="user_list"),
    path("v1/update_shop/", update_shop, name="update_shop"),
]