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
    path("test/ping/", test_ping_view, name="test_ping_view"),
    path("test/users/", test_user_list, name="test_user_list"),
    path(
        "test/do_authorized_action/",
        test_do_authorized_action,
        name="test_do_authorized_action",
    ),
    # other
    path("parnter/update/", update_shop, name="update_shop"),
    path("user/register/", register_user, name="register_user"),
    path("user/login/", login_user, name="login_user"),
    path("user/logout/", logout_user, name="logout_user"),
]
