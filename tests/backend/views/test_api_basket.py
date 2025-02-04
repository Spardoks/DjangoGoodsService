import json

import pytest
import yaml
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import (
    Category,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)
from backend.serializers import import_shop


@pytest.mark.django_db
def test_create_and_get_basket_example():
    shop = User.objects.create_user(email="shop@test.com", type="shop")
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    import_shop(shop, data)

    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password, type="buyer")

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    items = [
        {
            "product_info": 1,
            "quantity": 1,
        },
    ]
    assert ProductInfo.objects.filter(id=items[0]["product_info"]).exists()
    assert (
        ProductInfo.objects.get(id=items[0]["product_info"]).quantity
        >= items[0]["quantity"]
    )
    data = {
        "items": json.dumps(items),
    }
    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("basket")
    resp = client.post(url, data, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "created" in resp.json()
    assert resp.json()["created"] == 1

    assert Order.objects.count() == 1
    assert user.orders.count() == 1
    assert Order.objects.filter(user=user).exists()
    assert OrderItem.objects.count() == 1

    order_db = Order.objects.get(user=user)
    assert order_db.ordered_items.count() == 1
    assert order_db.state == "basket"

    order_item_db = OrderItem.objects.get(order=order_db)
    assert order_item_db.quantity == 1
    assert order_item_db.product_info.id == items[0]["product_info"]

    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "orders" in resp.json()
    orders = resp.json()["orders"]
    assert len(orders) == 1

    order = orders[0]
    assert "id" in order
    assert "ordered_items" in order
    assert "state" in order
    assert "dt" in order
    assert "total_sum" in order
    assert "contact" in order

    assert order["id"] == order_db.id
    assert order["state"] == order_db.state
    assert order["dt"] == order_db.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    assert order["total_sum"] == items[0]["quantity"] * order_item_db.product_info.price
    assert order["contact"] == None

    order_items = order["ordered_items"]
    assert len(order_items) == 1

    order_item = order_items[0]
    assert "id" in order_item
    assert "product_info" in order_item
    assert "quantity" in order_item
    assert "order" not in order_item

    assert order_item["id"] == order_item_db.id
    assert order_item["quantity"] == order_item_db.quantity
    assert order_item["quantity"] == items[0]["quantity"]

    product_info = order_item["product_info"]
    assert "id" in product_info
    assert "model" in product_info
    assert "product" in product_info
    assert "shop" in product_info
    assert "quantity" in product_info
    assert "price" in product_info
    assert "price_rrc" in product_info
    assert "product_parameters" in product_info

    prdouct_info_db = ProductInfo.objects.get(id=items[0]["product_info"])
    assert product_info["id"] == prdouct_info_db.id
    assert product_info["model"] == prdouct_info_db.model
    assert product_info["shop"] == Shop.objects.get(id=prdouct_info_db.shop_id).id
    assert product_info["quantity"] == prdouct_info_db.quantity
    assert product_info["price"] == prdouct_info_db.price
    assert product_info["price_rrc"] == prdouct_info_db.price_rrc

    assert "name" in product_info["product"]
    assert "category" in product_info["product"]

    assert product_info["product"]["name"] == prdouct_info_db.product.name
    assert product_info["product"]["category"] == prdouct_info_db.product.category.name

    product_parameters = product_info["product_parameters"]
    assert len(product_parameters) == prdouct_info_db.product_parameters.count()

    product_parametrs_db = ProductParameter.objects.filter(
        product_info=items[0]["product_info"]
    )
    for parameter in product_parameters:
        assert "parameter" in parameter
        assert "value" in parameter

        parameter_name = parameter["parameter"]
        parameter_value = parameter["value"]

        product_parametr_db = None
        for _ in product_parametrs_db:
            if _.parameter.name == parameter_name:
                product_parametr_db = _
                break
        assert product_parametr_db is not None
        assert product_parametr_db.value == parameter_value


@pytest.mark.django_db
def test_delete_order_items_example():
    shop = Shop.objects.create(name="test_shop")
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    product_info = ProductInfo.objects.create(
        product=product, shop=shop, quantity=10, price=100, price_rrc=200
    )

    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password, type="buyer")
    order = Order.objects.create(user=user, state="basket")
    quantity = 5
    order_item = OrderItem.objects.create(
        order=order, product_info=product_info, quantity=quantity
    )
    assert Order.objects.count() == 1
    assert order.ordered_items.count() == 1

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    params = {"items": str(order_item.id) + ","}
    url = reverse("basket")
    resp = client.delete(url, params, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "deleted" in resp.json()
    assert resp.json()["deleted"] == 1

    assert order.ordered_items.count() == 0
    assert Order.objects.count() == 1


@pytest.mark.django_db
def test_update_order_items_example():
    shop = Shop.objects.create(name="test_shop")
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    product_info = ProductInfo.objects.create(
        product=product, shop=shop, quantity=10, price=100, price_rrc=200
    )

    email = "test_user@test_mail.com"
    password = "test_password"
    user = User.objects.create_user(email=email, password=password, type="buyer")
    order = Order.objects.create(user=user, state="basket")
    quantity = 5
    order_item = OrderItem.objects.create(
        order=order, product_info=product_info, quantity=quantity
    )
    assert Order.objects.count() == 1
    assert order.ordered_items.count() == 1
    assert order_item.quantity == quantity

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    items = [
        {
            "order_item_id": order_item.id,
            "quantity": 2,
        },
    ]
    assert ProductInfo.objects.filter(id=items[0]["order_item_id"]).exists()
    assert (
        ProductInfo.objects.get(id=items[0]["order_item_id"]).quantity
        >= items[0]["quantity"]
    )
    assert items[0]["quantity"] != quantity
    data = {
        "items": json.dumps(items),
    }
    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("basket")
    resp = client.put(url, data, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "updated" in resp.json()
    assert resp.json()["updated"] == 1

    assert order.ordered_items.count() == 1
    assert Order.objects.count() == 1

    order_item_db = OrderItem.objects.get(id=order_item.id)
    assert order_item_db.quantity == items[0]["quantity"]
