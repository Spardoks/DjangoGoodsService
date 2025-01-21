# ToDo: разделить тесты api и добавить большее покрытие
import pytest
import yaml
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


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
def test_update_shop_by_url(base_test_users):
    user = base_test_users[3]
    assert user.type == "shop"

    params = {
        "url": "https://raw.githubusercontent.com/Spardoks/DjangoGoodsService/refs/heads/master/tests/backend/models/test_shop.yaml",
        "user": user.email,
    }
    client = APIClient()
    url = reverse("update_shop")
    resp = client.post(url, params)
    assert resp.status_code == 200

    resp_json = resp.json()
    assert "Status" in resp_json
    assert "url" in resp_json
    assert "user" in resp_json
    assert "data" in resp_json

    assert resp_json["Status"] == True
    assert resp_json["url"] == params["url"]
    assert resp_json["user"] == params["user"]

    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    assert resp_json["data"] == data

    result = resp_json
    assert "Status" in result
    assert "actual_categories_id" in result
    assert "actual_products_id" in result
    assert result["Status"] == True

    assert User.objects.count() == len(base_test_users)
    assert Shop.objects.count() == 1
    shop_by_user = Shop.objects.filter(user_id=user.id).first()
    shop_by_name = Shop.objects.filter(name=data["shop"]).first()
    assert shop_by_user == shop_by_name

    actual_categories_id = result["actual_categories_id"]
    actual_products_id = result["actual_products_id"]
    categories = data["categories"]
    goods = data["goods"]

    assert len(actual_categories_id) == len(categories)
    assert len(actual_products_id) == len(goods)
    assert Category.objects.count() == len(categories)
    assert Product.objects.count() == len(goods)
    assert ProductInfo.objects.count() == len(goods)
    shop = shop_by_name
    for item in goods:
        product = Product.objects.filter(id=actual_products_id[str(item["id"])]).first()
        assert product.name == item["name"]
        assert product.category_id == actual_categories_id[str(item["category"])]

        product_info = ProductInfo.objects.get(product_id=product.id)
        assert product_info.model == item["model"]
        assert product_info.price == item["price"]
        assert product_info.price_rrc == item["price_rrc"]
        assert product_info.quantity == item["quantity"]
        assert product_info.shop_id == shop.id

        assert product_info.product_parameters.count() == len(item["parameters"])
        for name, value in item["parameters"].items():
            parameter_object = Parameter.objects.filter(name=name).first()
            product_parameter = ProductParameter.objects.filter(
                product_info_id=product_info.id, parameter_id=parameter_object.id
            ).first()
            assert product_parameter.value == str(value)


@pytest.mark.django_db
def test_register_example():
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
    url = reverse("do_authorized_action")
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

    url = reverse("do_authorized_action")
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