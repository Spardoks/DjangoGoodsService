from django.urls import path
from django_rest_passwordreset.views import (
    reset_password_confirm,
    reset_password_request_token,
)

from backend.views import (
    BasketView,
    ConfirmAccount,
    ContactView,
    OrderView,
    PartnerOrderView,
    PartnerState,
    RegisterAccount,
    list_products,
    list_shops,
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
    path("partner/update/", update_shop, name="update_shop"),
    path("partner/state", PartnerState.as_view(), name="partner_state"),
    path("partner/orders/", PartnerOrderView.as_view(), name="partner_orders"),
    path("user/register/", register_user, name="register_user"),
    path("user/safe_register", RegisterAccount.as_view(), name="safe_register_user"),
    path(
        "user/safe_register/confirm",
        ConfirmAccount.as_view(),
        name="confirm_safe_register_user",
    ),
    # ToDo: override for common structure https://pypi.org/project/django-rest-passwordreset/
    path("user/password_reset", reset_password_request_token, name="password_reset"),
    # ToDo: override for common structure https://pypi.org/project/django-rest-passwordreset/
    path(
        "user/password_reset/confirm",
        reset_password_confirm,
        name="password_reset_confirm",
    ),
    path("user/login/", login_user, name="login_user"),
    path("user/logout/", logout_user, name="logout_user"),
    path("user/contact/", ContactView.as_view(), name="user-contact"),
    path("basket/", BasketView.as_view(), name="basket"),
    path("products/", list_products, name="list_products"),
    path("orders/", OrderView.as_view(), name="orders"),
    path("shops/", list_shops, name="list_shops"),
]
