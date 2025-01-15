import django
import pytest

from backend.models import Shop, Category, Product, ProductInfo


@pytest.mark.django_db
def test_create_productinfo_example():
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    shop = Shop.objects.create(name="test_shop")
    quantity = 10
    price = 100
    price_rrc = 200

    productinfo = ProductInfo.objects.create(product=product, shop=shop, quantity=quantity, price=price, price_rrc=price_rrc)

    assert ProductInfo.objects.count() == 1
    assert productinfo.product == product
    assert productinfo.shop == shop
    assert productinfo.quantity == quantity
    assert productinfo.price == price
    assert productinfo.price_rrc == price_rrc
    assert ProductInfo.objects.get(product=product, shop=shop) == productinfo
    assert product.product_infos.count() == 1
    assert product.product_infos.filter(shop=shop).exists()
    assert shop.product_infos.count() == 1
    assert shop.product_infos.filter(product=product).exists()