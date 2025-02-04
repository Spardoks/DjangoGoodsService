import pytest
import yaml
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import Category, User
from backend.serializers import import_shop


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
def test_list_products_no_shop_id():
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
