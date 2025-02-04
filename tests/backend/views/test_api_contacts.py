import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import Contact, User


@pytest.mark.django_db
def test_create_and_get_contact_example():
    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    contact_params = {
        "city": "test_city",
        "street": "test_street",
        "house": "test_house",
        "structure": "test_structure",
        "building": "test_building",
        "apartment": "test_apartment",
        "phone": "test_phone",
    }
    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("user-contact")
    resp = client.post(url, contact_params, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert Contact.objects.count() == 1
    contact_db = Contact.objects.get(user=user)
    assert contact_db.user == user
    assert contact_db.city == contact_params["city"]
    assert contact_db.street == contact_params["street"]
    assert contact_db.house == contact_params["house"]
    assert contact_db.structure == contact_params["structure"]
    assert contact_db.building == contact_params["building"]
    assert contact_db.apartment == contact_params["apartment"]
    assert contact_db.phone == contact_params["phone"]

    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True

    assert "contacts" in resp_json
    contacts = resp_json["contacts"]
    assert len(contacts) == 1

    contact = contacts[0]
    assert "user" not in contact
    assert "id" in contact
    assert "city" in contact
    assert "street" in contact
    assert "house" in contact
    assert "structure" in contact
    assert "building" in contact
    assert "apartment" in contact
    assert "phone" in contact

    assert contact["city"] == contact_params["city"]
    assert contact["street"] == contact_params["street"]
    assert contact["house"] == contact_params["house"]
    assert contact["structure"] == contact_params["structure"]
    assert contact["building"] == contact_params["building"]
    assert contact["apartment"] == contact_params["apartment"]
    assert contact["phone"] == contact_params["phone"]

    assert contact["id"] == Contact.objects.get(user=user).id


@pytest.mark.django_db
def test_delete_contact_example():
    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}

    contact_params = {
        "city": "test_city",
        "street": "test_street",
        "house": "test_house",
        "structure": "test_structure",
        "building": "test_building",
        "apartment": "test_apartment",
        "phone": "test_phone",
    }

    contact = Contact.objects.create(user=user, **contact_params)
    assert Contact.objects.count() == 1

    contact_id = Contact.objects.get(user=user).id
    delete_data = {"items": str(contact_id) + ","}
    url = reverse("user-contact")
    resp = client.delete(url, delete_data, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "deleted" in resp.json()
    assert resp.json()["deleted"] == 1

    with pytest.raises(Contact.DoesNotExist):
        Contact.objects.get(user=user)


@pytest.mark.django_db
def test_update_contact_example():
    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password)
    assert User.objects.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}

    contact_params = {
        "city": "test_city",
        "street": "test_street",
        "house": "test_house",
        "structure": "test_structure",
        "building": "test_building",
        "apartment": "test_apartment",
        "phone": "test_phone",
    }
    contact = Contact.objects.create(user=user, **contact_params)
    assert Contact.objects.count() == 1

    contact_params_updated = {
        "city": "test_city_updated",
        "street": "test_street",
        "house": "test_house",
        "structure": "test_structure",
        "building": "test_building",
        "apartment": "test_apartment",
        "phone": "test_phone",
        "id": str(contact.id),
    }
    url = reverse("user-contact")
    resp = client.put(url, contact_params_updated, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    contact_db_updated = Contact.objects.get(user=user)
    assert contact_db_updated is not None
    assert str(contact_db_updated.id) == contact_params_updated["id"]
    assert contact_db_updated.city == contact_params_updated["city"]
    assert contact_db_updated.street == contact_params_updated["street"]
    assert contact_db_updated.house == contact_params_updated["house"]
    assert contact_db_updated.structure == contact_params_updated["structure"]
    assert contact_db_updated.building == contact_params_updated["building"]
    assert contact_db_updated.apartment == contact_params_updated["apartment"]
    assert contact_db_updated.phone == contact_params_updated["phone"]
