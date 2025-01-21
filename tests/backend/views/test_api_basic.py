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
from backend.serializers import import_shop


def test_ping_view():
    client = APIClient()
    url = reverse("test_ping_view")
    resp = client.get(url)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True


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

    client = APIClient()
    url = reverse("logout_user")
    resp = client.post(url, headers={})
    assert resp.status_code == 403
    resp_json = resp.json()
    assert "Status" in resp_json
    assert "Error" in resp_json
    assert resp_json["Status"] == False
    assert resp_json["Error"] == "Пользователь не опознан"


# ToDo: если магазинов будет больше, добавить тестов
@pytest.mark.django_db
def test_list_products_example():
    shop = User.objects.create_user(email="shop@test.com", type="shop")
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    result = import_shop(shop, data)

    client = APIClient()
    url = reverse("list_products")
    resp = client.get(url)
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert "products" in resp_json
    assert resp_json["Status"] == True

    items = resp_json["products"]
    assert len(items) == len(data["goods"])

    for item in items:
        assert "id" in item, item
        assert "model" in item, item
        assert "product" in item, item
        assert "shop" in item, item
        assert "quantity" in item, item
        assert "price" in item, item
        assert "price_rrc" in item, item
        assert "product_parameters" in item, item

        assert "name" in item["product"], item
        assert "category" in item["product"], item

    actual_categories_id = result["actual_categories_id"]
    actual_products_id = result["actual_products_id"]
    goods = data["goods"]

    for good in goods:
        good_id = good["id"]
        item_id = actual_products_id[good_id]
        item = None
        for _ in items:
            if _["id"] == item_id:
                item = _
        assert (
            item is not None
        ), f"Product with id {good_id} not found after getting list of products for shop {shop.id}"

        assert item["model"] == good["model"], item
        assert item["product"]["name"] == good["name"], item
        assert (
            item["product"]["category"]
            == Category.objects.get(id=actual_categories_id[good["category"]]).name
        ), item
        assert item["shop"] == shop.id, item
        assert item["quantity"] == good["quantity"], item
        assert item["price"] == good["price"], item
        assert item["price_rrc"] == good["price_rrc"], item

        item_product_parameters = item["product_parameters"]
        assert len(item_product_parameters) == len(good["parameters"]), item
        for name, value in good["parameters"].items():
            item_parametr = None
            for _ in item_product_parameters:
                assert "parameter" in _, item
                if _["parameter"] == name:
                    item_parametr = _
            assert item_parametr is not None, item
            assert item_parametr["value"] == str(value), item


@pytest.mark.django_db
def test_list_shops_no_shop_id():
    shop = User.objects.create_user(email="shop@test.com", type="shop")
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    result = import_shop(shop, data)

    client = APIClient()
    url = reverse("list_products")
    params = {"shop_id": shop.id + 1}
    resp = client.get(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert resp_json["Status"] == True

    assert "products" in resp_json
    assert resp_json["products"] == []


@pytest.mark.django_db
def test_list_products_special_category_and_shop():
    shop = User.objects.create_user(email="shop@test.com", type="shop")
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    result = import_shop(shop, data)

    actual_categories_id = result["actual_categories_id"]
    actual_products_id = result["actual_products_id"]
    goods = data["goods"]

    category_goods_id = data["categories"][0]["id"]
    actual_category_goods_id = actual_categories_id[category_goods_id]
    actual_products_id_by_category = {}
    category_goods = []
    for good in goods:
        if good["category"] == category_goods_id:
            category_goods.append(good)
            actual_products_id_by_category[good["id"]] = actual_products_id[good["id"]]

    params = {"category_id": actual_category_goods_id, "shop_id": shop.id}
    client = APIClient()
    url = reverse("list_products")
    resp = client.get(url, params)
    assert resp.status_code == 200, resp.json()["Error"]

    resp_json = resp.json()
    assert "Status" in resp_json
    assert "products" in resp_json
    assert resp_json["Status"] == True

    items = resp_json["products"]
    assert len(items) == len(category_goods)

    for item in items:
        assert "id" in item, item
        assert "model" in item, item
        assert "product" in item, item
        assert "shop" in item, item
        assert "quantity" in item, item
        assert "price" in item, item
        assert "price_rrc" in item, item
        assert "product_parameters" in item, item

        assert "name" in item["product"], item
        assert "category" in item["product"], item

    for good in category_goods:
        good_id = good["id"]
        item_id = actual_products_id_by_category[good_id]
        item = None
        for _ in items:
            if _["id"] == item_id:
                item = _
        assert (
            item is not None
        ), f"Product with id {good_id} not found after getting list of products for shop {shop.id} with category {category_goods_id}"

        assert item["model"] == good["model"], item
        assert item["product"]["name"] == good["name"], item
        assert (
            item["product"]["category"]
            == Category.objects.get(id=actual_category_goods_id).name
        ), item
        assert item["shop"] == shop.id, item
        assert item["quantity"] == good["quantity"], item
        assert item["price"] == good["price"], item
        assert item["price_rrc"] == good["price_rrc"], item

        item_product_parameters = item["product_parameters"]
        assert len(item_product_parameters) == len(good["parameters"]), item
        for name, value in good["parameters"].items():
            item_parametr = None
            for _ in item_product_parameters:
                assert "parameter" in _, item
                if _["parameter"] == name:
                    item_parametr = _
            assert item_parametr is not None, item
            assert item_parametr["value"] == str(value), item
