import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    Shop,
    User,
)


@pytest.mark.django_db
def test_create_and_get_order_example():
    user_shop_email = "shop@test.com"
    user_shop_db = User.objects.create_user(email=user_shop_email, type="shop")
    shop_db = Shop.objects.create(name="test_shop", user=user_shop_db, state=True)
    category_db = Category.objects.create(name="test_category")
    product_db = Product.objects.create(name="test_product", category=category_db)
    product_info_db = ProductInfo.objects.create(
        product=product_db, shop=shop_db, quantity=10, price=100, price_rrc=200
    )

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "noreply@goods_service.com"

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

    assert "orders" in resp.json()
    assert len(resp.json()["orders"]) == 1

    assert Order.objects.count() == 1
    assert Order.objects.filter(id=order_db.id).exists() == False

    assert Order.objects.filter(id=resp.json()["orders"][0]).exists()
    order_db = Order.objects.get(id=resp.json()["orders"][0])

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

    # Проверка, что письмо было отправлено
    assert len(mail.outbox) == 2
    assert mail.outbox[0].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[0].body == f"Смотрите заказ {order_db.id}"
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [email]

    assert mail.outbox[1].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[1].body == f"Смотрите заказ {order_db.id}"
    assert mail.outbox[1].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[1].to == [user_shop_email]


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

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "noreply@goods_service.com"

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

    # Проверка, что письмо было отправлено
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[0].body == f"Смотрите заказ {order_db.id}"
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [email]


@pytest.mark.django_db
def test_create_and_get_orders_from2shops_example():
    user_shop_email1 = "shop@test.com"
    user_shop_db1 = User.objects.create_user(email=user_shop_email1, type="shop")
    shop_db1 = Shop.objects.create(name="test_shop", user=user_shop_db1, state=True)
    category_db1 = Category.objects.create(name="test_category")
    product_db1 = Product.objects.create(name="test_product", category=category_db1)
    product_info_db1 = ProductInfo.objects.create(
        product=product_db1, shop=shop_db1, quantity=10, price=100, price_rrc=200
    )

    user_shop_email2 = "shop2@test.com"
    user_shop_db2 = User.objects.create_user(email=user_shop_email2, type="shop")
    shop_db2 = Shop.objects.create(name="test_shop2", user=user_shop_db2, state=True)
    category_db2 = Category.objects.create(name="test_category2")
    product_db2 = Product.objects.create(name="test_product2", category=category_db2)
    product_info_db2 = ProductInfo.objects.create(
        product=product_db2, shop=shop_db2, quantity=10, price=100, price_rrc=200
    )

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "noreply@goods_service.com"

    email = "test_user@test_mail.com"
    password = "test_password"
    user_db = User.objects.create_user(email=email, password=password, type="buyer")
    order_db = Order.objects.create(user=user_db, state="basket")
    quantity1 = 5
    order_item_db1 = OrderItem.objects.create(
        order=order_db, product_info=product_info_db1, quantity=quantity1
    )

    quantity2 = 3
    order_item_db2 = OrderItem.objects.create(
        order=order_db, product_info=product_info_db2, quantity=quantity2
    )

    assert Order.objects.count() == 1
    assert order_db.ordered_items.count() == 2
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

    assert "orders" in resp.json()
    assert len(resp.json()["orders"]) == 2

    assert Order.objects.count() == 2
    assert Order.objects.filter(id=order_db.id).exists() == False

    assert Order.objects.filter(id=resp.json()["orders"][0]).exists()
    assert Order.objects.filter(id=resp.json()["orders"][1]).exists()

    created_orders = Order.objects.filter(user=user_db)
    created_orders = created_orders.order_by("id")

    for order in created_orders:
        assert order.state == "new"
        assert order.contact is not None
        assert order.contact == contact_db



    resp = client.get(url, headers=header)
    assert resp.status_code == 200, resp.json()["Error"]
    assert "Status" in resp.json()
    assert resp.json()["Status"] == True

    assert "orders" in resp.json()
    assert len(resp.json()["orders"]) == 2

    reference_data = {"quantity": [quantity1, quantity2], "price": [100, 100]}
    reference_data["order_item_id"] = [order_item_db1.id, order_item_db2.id]
    reference_data["product_info"] = {}
    reference_data["product_info"]["id"] = [product_info_db1.id, product_info_db2.id]
    reference_data["product_info"]["model"] = [product_info_db1.model, product_info_db2.model]
    reference_data["product_info"]["shop_id"] = [shop_db1.id, shop_db2.id]
    reference_data["product_info"]["quantity"] = [
        product_info_db1.quantity,
        product_info_db2.quantity,
    ]
    reference_data["product_info"]["price"] = [
        product_info_db1.price,
        product_info_db2.price,
    ]
    reference_data["product_info"]["price_rrc"] = [
        product_info_db1.price_rrc,
        product_info_db2.price_rrc,
    ]
    reference_data["product"] = {}
    reference_data["product"]["name"] = [product_db1.name, product_db2.name]
    reference_data["product"]["category"] = [category_db1.name, category_db2.name]

    for i in range(2):
        order = resp.json()["orders"][i]
        order_db = created_orders[i]

        assert "id" in order
        assert "state" in order
        assert "dt" in order
        assert "total_sum" in order
        assert "contact" in order
        assert "ordered_items" in order

        assert order["id"] == order_db.id
        assert order["state"] == order_db.state
        assert order["dt"] == order_db.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        assert (
            order["total_sum"]
            == reference_data["quantity"][i] * reference_data["price"][i]
        )
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

        assert order_item["id"] == reference_data["order_item_id"][i]
        assert order_item["quantity"] == reference_data["quantity"][i]

        product_info = order_item["product_info"]
        assert "id" in product_info
        assert "model" in product_info
        assert "product" in product_info
        assert "shop" in product_info
        assert "quantity" in product_info
        assert "price" in product_info
        assert "price_rrc" in product_info
        assert "product_parameters" in product_info

        assert product_info["id"] == reference_data["product_info"]["id"][i]
        assert product_info["model"] == reference_data["product_info"]["model"][i]
        assert product_info["shop"] == reference_data["product_info"]["shop_id"][i]
        assert product_info["quantity"] == reference_data["product_info"]["quantity"][i]
        assert product_info["price"] == reference_data["product_info"]["price"][i]
        assert (
            product_info["price_rrc"] == reference_data["product_info"]["price_rrc"][i]
        )
        assert len(product_info["product_parameters"]) == 0

        assert "name" in product_info["product"]
        assert "category" in product_info["product"]

        assert (
            product_info["product"]["name"]
            == reference_data["product"]["name"][i]
        )
        assert (
            product_info["product"]["category"]
            == reference_data["product"]["category"][i]
        )

    created_orders_sorted_ids = [order.id for order in created_orders]
    created_orders_sorted_ids.sort()

    # Проверка, что письмо было отправлено
    assert len(mail.outbox) == 4
    assert mail.outbox[0].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[0].body == f"Смотрите заказ {created_orders_sorted_ids[0]}"
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [email]

    assert mail.outbox[1].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[1].body == f"Смотрите заказ {created_orders_sorted_ids[0]}"
    assert mail.outbox[1].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[1].to == [user_shop_email1]

    assert mail.outbox[2].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[2].body == f"Смотрите заказ {created_orders_sorted_ids[1]}"
    assert mail.outbox[2].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[2].to == [email]

    assert mail.outbox[3].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[3].body == f"Смотрите заказ {created_orders_sorted_ids[1]}"
    assert mail.outbox[3].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[3].to == [user_shop_email2]
