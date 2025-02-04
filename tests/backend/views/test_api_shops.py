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


@pytest.fixture
def base_test_users():
    user1 = User.objects.create_user(email="test1@test.com", type="buyer")
    user2 = User.objects.create_user(email="test2@test.com", type="buyer")
    user3 = User.objects.create_user(email="test3@test.com", type="shop")
    user4 = User.objects.create_user(email="test4@test.com", type="shop")

    return [user1, user2, user3, user4]


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
def test_get_shops_list():
    shop_user_db = User.objects.create_user(email="shop@test.com", type="shop")
    shop_db = Shop.objects.create(
        name="test_shop", user=shop_user_db, state=True, url="https://test_shop.com"
    )

    client = APIClient()
    url = reverse("list_shops")
    params = {"shop_id": shop_db.id}  # or empty for all shops
    resp = client.get(url, params)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "shops" in resp.json()
    assert len(resp.json()["shops"]) == 1

    shop = resp.json()["shops"][0]
    assert "id" in shop
    assert "name" in shop
    assert "state" in shop
    assert "url" in shop
    assert "contact" in shop

    assert shop["id"] == shop_db.id
    assert shop["name"] == shop_db.name
    assert shop["state"] == shop_db.state
    assert shop["url"] == shop_db.url

    assert "email" in shop["contact"]
    assert shop["contact"]["email"] == shop_user_db.email


@pytest.mark.django_db
def test_change_shop_state_example():
    email = "test1@test.com"
    password = "test_password"
    shop_user_db = User.objects.create_user(email=email, password=password, type="shop")
    first_state = True
    shop_db = Shop.objects.create(
        name="test_shop",
        user=shop_user_db,
        state=first_state,
        url="https://test_shop.com",
    )
    assert shop_db.state == first_state

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("partner_state")
    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "state" in resp.json()
    assert resp.json()["state"] == first_state

    second_state = False
    data = {"state": second_state}
    url = reverse("partner_state")
    resp = client.post(url, data, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    shop_db.refresh_from_db()
    assert shop_db.state == second_state
