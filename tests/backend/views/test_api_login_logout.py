import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import User


@pytest.mark.django_db
def test_register_buyer_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    client = APIClient()
    url = reverse("register_user")
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


@pytest.mark.django_db
def test_register_shop_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "shop",
    }

    client = APIClient()
    url = reverse("register_user")
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


@pytest.mark.django_db
def test_register_invalid_type_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "client",
    }

    client = APIClient()
    url = reverse("register_user")
    resp = client.post(url, params)
    assert resp.status_code == 403, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == False
    assert "Error" in resp_json
    assert resp_json["Error"] == "Неверный тип пользователя"


@pytest.mark.django_db
def test_register_duplicate_email_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    client = APIClient()
    url = reverse("register_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp = client.post(url, params)
    assert resp.status_code == 403, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == False
    assert "Error" in resp_json
    assert resp_json["Error"] == "Пользователь уже существует"

    assert User.objects.count() == 1


@pytest.mark.django_db
def test_login_and_do_authorized_action_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert "token" in resp_json
    assert resp_json["Status"] == True
    assert resp_json["token"] is not None

    header = {"Authorization": f"Token {resp_json['token']}"}
    url = reverse("test_do_authorized_action")
    resp = client.post(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    resp = client.post(url, headers={})
    assert resp.status_code == 403
    assert "Status" in resp.json()
    assert "Error" in resp.json()
    assert resp.json()["Status"] == False
    assert resp.json()["Error"] == "Пользователь не опознан"


@pytest.mark.django_db
def test_logout_example():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("logout_user")
    resp = client.post(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]

    url = reverse("test_do_authorized_action")
    resp = client.post(url, headers=header)
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Пользователь не авторизован"


@pytest.mark.django_db
def test_login_logout_twice():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    resp = client.post(url, params, headers=header)
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Пользователь уже авторизован"

    url = reverse("logout_user")
    resp = client.post(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]

    resp = client.post(url, headers=header)
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Пользователь не авторизован"


@pytest.mark.django_db
def test_login_no_token_after_success_login():
    params = {
        "email": "test_user@test_mail.com",
        "password": "test_password",
        "type": "buyer",
    }

    user = User.objects.create_user(**params)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp = client.post(url, params)
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Не удалось создать токен"


@pytest.mark.django_db
def test_logout_no_token():
    client = APIClient()
    url = reverse("logout_user")
    resp = client.post(url, headers={})
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Пользователь не опознан"