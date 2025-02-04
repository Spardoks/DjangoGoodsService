import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import User


@pytest.fixture
def base_test_users():
    user1 = User.objects.create_user(email="test1@test.com", type="buyer")
    user2 = User.objects.create_user(email="test2@test.com", type="buyer")
    user3 = User.objects.create_user(email="test3@test.com", type="shop")
    user4 = User.objects.create_user(email="test4@test.com", type="shop")

    return [user1, user2, user3, user4]


def test_ping_view():
    client = APIClient()
    url = reverse("test_ping_view")
    resp = client.get(url)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True


@pytest.mark.django_db
def test_user_list(base_test_users):
    client = APIClient()
    url = reverse("test_user_list")
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Status" in resp.json()
    assert "users" in resp.json()

    resp_json = resp.json()
    assert resp_json["Status"] == True
    users = resp_json["users"]
    assert len(users) == len(base_test_users)

    got_emails = [u["email"] for u in users]
    for user in base_test_users:
        assert user.email in got_emails
