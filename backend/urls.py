from django.urls import path

from backend.views import (
    login_user,
    logout_user,
    register_user,
    test_do_authorized_action,
    test_ping_view,
    test_user_list,
    update_shop,
)

urlpatterns = [
    # test
    path("v1/ping/", test_ping_view, name="test_ping_view"),
    path("v1/users/", test_user_list, name="test_user_list"),
    path(
        "v1/do_authorized_action/",
        test_do_authorized_action,
        name="test_do_authorized_action",
    ),
    # other
    path("v1/update_shop/", update_shop, name="update_shop"),
    path("v1/register_user/", register_user, name="register_user"),
    path("v1/login_user/", login_user, name="login_user"),
    path("v1/logout_user/", logout_user, name="logout_user"),
]
