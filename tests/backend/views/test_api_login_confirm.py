import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse
from django_rest_passwordreset.models import ResetPasswordToken
from rest_framework.test import APIClient

from backend.models import ConfirmEmailToken, User


@pytest.mark.django_db
def test_safe_register_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    client = APIClient()
    url = reverse("safe_register_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True

    assert User.objects.count() == 1
    user = User.objects.filter(email=params["email"]).first()
    assert user is not None
    assert user.email == params["email"]
    assert user.type == params["type"]
    assert user.is_active == False

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": params["password"]})
    assert resp.status_code == 403, resp.json()["Error"]

    assert "Error" in resp.json()
    assert resp.json()["Error"] == "Пользователь не активирован"

    assert user.is_active == False


@pytest.mark.django_db
def test_confirm_safe_db_register_email_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params, is_active=False)
    assert User.objects.count() == 1
    assert user.is_active == False

    token = ConfirmEmailToken.objects.create(user=user)
    assert ConfirmEmailToken.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": params["password"]})
    assert resp.status_code == 403, resp.json()["Error"]
    assert "Error" in resp.json()
    assert resp.json()["Error"] == "Пользователь не активирован"

    client = APIClient()
    url = reverse("confirm_safe_register_user")
    resp = client.post(url, {"email": params["email"], "token": token.key})
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True

    user.refresh_from_db()
    assert user.is_active == True

    assert ConfirmEmailToken.objects.count() == 0

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": params["password"]})
    assert resp.status_code == 200, resp.json()["Error"]


@pytest.mark.django_db
def test_confirm_safe_api_register_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "noreply@goods_service.com"

    client = APIClient()
    url = reverse("safe_register_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    token = ConfirmEmailToken.objects.filter(user__email=params["email"]).first()
    assert token is not None

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == f"Registration Token for {params['email']}"
    assert mail.outbox[0].body == token.key
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [params["email"]]

    client = APIClient()
    url = reverse("confirm_safe_register_user")
    resp = client.post(url, {"email": params["email"], "token": token.key})
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True

    user = User.objects.filter(email=params["email"]).first()
    assert user.is_active == True


@pytest.mark.django_db
def test_password_reset_example():
    params = {
        "email": "test@mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params)
    assert User.objects.count() == 1
    assert user.email == params["email"]

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "noreply@goods_service.com"

    client = APIClient()
    url = reverse("password_reset")
    resp = client.post(url, {"email": params["email"]})
    assert resp.status_code == 200

    assert ResetPasswordToken.objects.count() == 1
    token = ResetPasswordToken.objects.filter(user__email=params["email"]).first()
    assert token is not None

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == f"Password Reset Token for {params['email']}"
    assert mail.outbox[0].body == token.key
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [params["email"]]

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": params["password"]})
    assert resp.status_code == 200

    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("logout_user")
    resp = client.post(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]

    new_password = "newpassord"
    client = APIClient()
    url = reverse("password_reset_confirm")
    resp = client.post(url, {"token": token.key, "password": new_password})
    assert resp.status_code == 200
    ResetPasswordToken.objects.count() == 0

    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": params["password"]})
    assert resp.status_code == 403, resp.json()["Error"]

    assert "Error" in resp.json()
    assert resp.json()["Error"] == "Неверный пароль", resp.json()["Error"]

    url = reverse("login_user")
    resp = client.post(url, {"email": params["email"], "password": new_password})
    assert resp.status_code == 200, resp.json()["Error"]
