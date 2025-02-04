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
    shop_db = Shop.objects.create(name="test_shop")
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
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Обновление статуса/создание заказа"
    assert mail.outbox[0].body == f"Смотрите заказ {order_db.id}"
    assert mail.outbox[0].from_email == settings.EMAIL_HOST_USER
    assert mail.outbox[0].to == [email]


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
