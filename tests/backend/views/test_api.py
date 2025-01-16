import pytest
import yaml
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import User


def test_ping_view():
    client = APIClient()
    url = reverse("ping_view")
    resp = client.get(url)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["status"] == "OK"


@pytest.fixture
def base_test_users():
    user1 = User.objects.create_user(email="test1@test.com", type="buyer")
    user2 = User.objects.create_user(email="test2@test.com", type="buyer")
    user3 = User.objects.create_user(email="test3@test.com", type="shop")
    user4 = User.objects.create_user(email="test4@test.com", type="shop")

    return [user1, user2, user3, user4]


@pytest.mark.django_db
def test_user_list(base_test_users):
    client = APIClient()
    url = reverse("user_list")
    resp = client.get(url)
    assert resp.status_code == 200

    resp_json = resp.json()
    assert len(resp_json) == len(base_test_users)

    got_emails = [u["email"] for u in resp_json]
    for user in base_test_users:
        assert user.email in got_emails


@pytest.mark.django_db
def test_update_shop_url():
    client = APIClient()
    url = reverse("update_shop")
    params = {
        "url": "https://raw.githubusercontent.com/Spardoks/DjangoGoodsService/refs/heads/master/tests/backend/models/test_shop.yaml",
        "user": "test1@test.com",
    }
    resp = client.post(url, params)
    assert resp.status_code == 200

    resp_json = resp.json()
    assert "url" in resp_json
    assert "user" in resp_json
    assert "data" in resp_json

    assert resp_json["url"] == params["url"]
    assert resp_json["user"] == params["user"]

    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    assert resp_json["data"] == data
