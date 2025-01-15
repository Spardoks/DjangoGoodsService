import django
import pytest

from backend.models import Category, Product


@pytest.mark.django_db
def test_create_product_default():
    category = Category.objects.create(name="test_category")
    product_name = "test_product"

    product = Product.objects.create(name=product_name, category=category)

    assert Product.objects.count() == 1
    assert product.name == product_name
    assert product.category == category
    assert Product.objects.get(name=product_name) == product
    assert category.products.count() == 1
    assert category.products.filter(name=product_name).exists()


@pytest.mark.django_db
def test_create_product_without_category():
    product_name = "test_product"

    with pytest.raises(django.db.utils.IntegrityError):
        product = Product.objects.create(name=product_name)