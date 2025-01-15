import django
import pytest

from backend.models import (Category, Order, OrderItem, Product, ProductInfo,
                            Shop, User)


@pytest.mark.django_db
def test_create_orderitem_example():
    user = User.objects.create_user(email="test_user@test_mail.com")
    order = Order.objects.create(user=user)
    shop = Shop.objects.create(name="test_shop")
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    product_info = ProductInfo.objects.create(
        product=product, shop=shop, quantity=10, price=100, price_rrc=200
    )
    quantity = 5

    order_item = OrderItem.objects.create(
        order=order, product_info=product_info, quantity=quantity
    )

    assert OrderItem.objects.count() == 1
    assert order_item.order == order
    assert order_item.product_info == product_info
    assert order_item.quantity == quantity
    assert OrderItem.objects.get(order=order, product_info=product_info) == order_item
    assert order.ordered_items.count() == 1
    assert order.ordered_items.filter(product_info=product_info).exists()
    assert product_info.ordered_items.count() == 1
    assert product_info.ordered_items.filter(order=order).exists()


@pytest.mark.django_db
def test_create_orderitem_without_some_fields():
    user = User.objects.create_user(email="test_user@test_mail.com")
    order = Order.objects.create(user=user)
    shop = Shop.objects.create(name="test_shop")
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    product_info = ProductInfo.objects.create(
        product=product, shop=shop, quantity=10, price=100, price_rrc=200
    )
    quantity = 5

    with pytest.raises(django.db.utils.IntegrityError):
        OrderItem.objects.create(order=order, quantity=quantity)

    with pytest.raises(django.db.transaction.TransactionManagementError):
        OrderItem.objects.create(product_info=product_info, quantity=quantity)

    with pytest.raises(django.db.transaction.TransactionManagementError):
        OrderItem.objects.create(quantity=quantity)

    with pytest.raises(django.db.transaction.TransactionManagementError):
        OrderItem.objects.create(order=order, product_info=product_info)