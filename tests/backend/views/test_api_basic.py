# ToDo: разделить тесты api и добавить большее покрытие
import json

import pytest
import yaml
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
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


# import_shop
############################################


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


# list_products
############################################


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


# contact
############################################


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


# basket
#############################################


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


# orders
##############################################


@pytest.mark.django_db
def test_create_and_get_order_example():
    shop_db = Shop.objects.create(name="test_shop")
    category_db = Category.objects.create(name="test_category")
    product_db = Product.objects.create(name="test_product", category=category_db)
    product_info_db = ProductInfo.objects.create(
        product=product_db, shop=shop_db, quantity=10, price=100, price_rrc=200
    )

    email = "test_user@test_mail.com"
    password = "test_password"
    user_db = User.objects.create_user(email=email, password=password, type="buyer")
    order_db = Order.objects.create(user=user_db, state="basket")
    quantity = 5
    order_item_db = OrderItem.objects.create(
        order=order_db, product_info=product_info_db, quantity=quantity
    )
    assert Order.objects.count() == 1
    assert order_db.ordered_items.count() == 1
    assert order_db.contact is None

    city = "test_city"
    street = "test_street"
    house = "test_house"
    structure = "test_structure"
    building = "test_building"
    apartment = "test_apartment"
    phone = "test_phone"
    contact_db = Contact.objects.create(
        user=user_db,
        city=city,
        street=street,
        house=house,
        structure=structure,
        building=building,
        apartment=apartment,
        phone=phone,
    )

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": email, "password": password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    params = {"basket_id": order_db.id, "contact_id": contact_db.id}
    url = reverse("orders")
    resp = client.post(url, params, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    order_db = Order.objects.get(id=order_db.id)
    assert order_db.state == "new"
    assert order_db.contact is not None
    assert order_db.contact.id == contact_db.id

    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "orders" in resp.json()
    assert len(resp.json()["orders"]) == 1

    order = resp.json()["orders"][0]
    assert "id" in order
    assert "state" in order
    assert "dt" in order
    assert "total_sum" in order
    assert "contact" in order
    assert "ordered_items" in order

    assert order["id"] == order_db.id
    assert order["state"] == order_db.state
    assert order["dt"] == order_db.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    assert order["total_sum"] == quantity * order_item_db.product_info.price
    assert order["contact"] is not None
    assert order["ordered_items"] is not None

    contact = order["contact"]
    assert "id" in contact
    assert "city" in contact
    assert "street" in contact
    assert "house" in contact
    assert "structure" in contact
    assert "building" in contact
    assert "apartment" in contact
    assert "phone" in contact

    assert contact["id"] == contact_db.id
    assert contact["city"] == contact_db.city
    assert contact["street"] == contact_db.street
    assert contact["house"] == contact_db.house
    assert contact["structure"] == contact_db.structure
    assert contact["building"] == contact_db.building
    assert contact["apartment"] == contact_db.apartment
    assert contact["phone"] == contact_db.phone

    assert len(order["ordered_items"]) == 1
    order_item = order["ordered_items"][0]

    assert "id" in order_item
    assert "product_info" in order_item
    assert "quantity" in order_item
    assert "order" not in order_item

    assert order_item["id"] == order_item_db.id
    assert order_item["quantity"] == order_item_db.quantity
    assert order_item["quantity"] == quantity

    product_info = order_item["product_info"]
    assert "id" in product_info
    assert "model" in product_info
    assert "product" in product_info
    assert "shop" in product_info
    assert "quantity" in product_info
    assert "price" in product_info
    assert "price_rrc" in product_info
    assert "product_parameters" in product_info

    assert product_info["id"] == product_info_db.id
    assert product_info["model"] == product_info_db.model
    assert product_info["shop"] == product_info_db.shop.id
    assert product_info["quantity"] == product_info_db.quantity
    assert product_info["price"] == product_info_db.price
    assert product_info["price_rrc"] == product_info_db.price_rrc
    assert len(product_info["product_parameters"]) == 0

    assert "name" in product_info["product"]
    assert "category" in product_info["product"]

    assert product_info["product"]["name"] == product_db.name
    assert product_info["product"]["category"] == product_db.category.name


@pytest.mark.django_db
def test_get_and_update_shop_order_example():
    shop_email = "shop@test.com"
    shop_password = "shop_password"
    shop_user_db = User.objects.create_user(
        email=shop_email, password=shop_password, type="shop"
    )

    shop_db = Shop.objects.create(name="test_shop", user=shop_user_db, state=True)
    category_db = Category.objects.create(name="test_category")
    product_db = Product.objects.create(name="test_product", category=category_db)
    product_info_db = ProductInfo.objects.create(
        product=product_db, shop=shop_db, quantity=10, price=100, price_rrc=200
    )

    email = "test_user@test_mail.com"
    password = "test_password"
    user_db = User.objects.create_user(email=email, password=password, type="buyer")
    order_db = Order.objects.create(user=user_db, state="basket")
    quantity = 5
    order_item_db = OrderItem.objects.create(
        order=order_db, product_info=product_info_db, quantity=quantity
    )
    assert Order.objects.count() == 1
    assert order_db.ordered_items.count() == 1
    assert order_db.contact is None

    city = "test_city"
    street = "test_street"
    house = "test_house"
    structure = "test_structure"
    building = "test_building"
    apartment = "test_apartment"
    phone = "test_phone"
    contact_db = Contact.objects.create(
        user=user_db,
        city=city,
        street=street,
        house=house,
        structure=structure,
        building=building,
        apartment=apartment,
        phone=phone,
    )

    order_db.contact = contact_db
    order_db.state = "new"
    order_db.save()

    client = APIClient()
    url = reverse("login_user")
    resp = client.post(url, {"email": shop_email, "password": shop_password})
    assert resp.status_code == 200, resp.json()["Error"]

    header = {"Authorization": f"Token {resp.json()['token']}"}
    url = reverse("partner_orders")
    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "orders" in resp.json()
    assert len(resp.json()["orders"]) == 1

    order = resp.json()["orders"][0]
    assert "id" in order
    assert "ordered_items" in order
    assert "state" in order
    assert "dt" in order
    assert "total_sum" in order
    assert "contact" in order

    assert order["id"] == order_db.id
    assert order["state"] == order_db.state
    assert order["state"] != "basket"
    assert order["dt"] == order_db.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    assert order["total_sum"] == quantity * order_item_db.product_info.price
    assert order["contact"] is not None
    assert order["ordered_items"] is not None

    contact = order["contact"]
    assert "id" in contact
    assert "city" in contact
    assert "street" in contact
    assert "house" in contact
    assert "structure" in contact
    assert "building" in contact
    assert "apartment" in contact
    assert "phone" in contact

    assert contact["id"] == contact_db.id
    assert contact["city"] == contact_db.city
    assert contact["street"] == contact_db.street
    assert contact["house"] == contact_db.house
    assert contact["structure"] == contact_db.structure
    assert contact["building"] == contact_db.building
    assert contact["apartment"] == contact_db.apartment
    assert contact["phone"] == contact_db.phone

    assert len(order["ordered_items"]) == 1
    order_item = order["ordered_items"][0]

    assert "id" in order_item
    assert "product_info" in order_item
    assert "quantity" in order_item
    assert "order" not in order_item

    assert order_item["id"] == order_item_db.id
    assert order_item["quantity"] == order_item_db.quantity
    assert order_item["quantity"] == quantity

    product_info = order_item["product_info"]
    assert "id" in product_info
    assert "model" in product_info
    assert "product" in product_info
    assert "shop" in product_info
    assert "quantity" in product_info
    assert "price" in product_info
    assert "price_rrc" in product_info
    assert "product_parameters" in product_info

    assert product_info["id"] == product_info_db.id
    assert product_info["model"] == product_info_db.model
    assert product_info["shop"] == product_info_db.shop.id
    assert product_info["quantity"] == product_info_db.quantity
    assert product_info["price"] == product_info_db.price
    assert product_info["price_rrc"] == product_info_db.price_rrc
    assert len(product_info["product_parameters"]) == 0

    assert "name" in product_info["product"]
    assert "category" in product_info["product"]

    assert product_info["product"]["name"] == product_db.name
    assert product_info["product"]["category"] == product_db.category.name

    data = {"order_id": order_db.id, "state": "confirmed"}
    url = reverse("partner_orders")
    resp = client.post(url, data, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    order_db.refresh_from_db()
    assert order_db.state == "confirmed"


# shops
##############################################


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
