from django.urls import path

from backend.views import (
    do_authorized_action,
    login_user,
    ping_view,
    register_user,
    update_shop,
    user_list,
)

urlpatterns = [
    path("v1/ping/", ping_view, name="ping_view"),
    path("v1/users/", user_list, name="user_list"),
    path("v1/update_shop/", update_shop, name="update_shop"),
    path("v1/register_user/", register_user, name="register_user"),
    path("v1/login_user/", login_user, name="login_user"),
    path("v1/do_authorized_action/", do_authorized_action, name="do_authorized_action"),
]
