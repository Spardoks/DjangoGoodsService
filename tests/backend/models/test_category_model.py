import django
import pytest

from backend.models import Shop, Category


@pytest.mark.django_db
def test_create_category_default():
    category_name = "test_category"

    category = Category.objects.create(name=category_name)

    assert category.name == category_name
    assert category.shops.count() == 0


@pytest.mark.django_db
def test_create_category_with_shops():
    shop1 = Shop.objects.create(name="test_shop1")
    shop2 = Shop.objects.create(name="test_shop2")
    category_name = "test_category"
    category = Category.objects.create(name=category_name)

    category.shops.add(shop1)
    category.shops.add(shop2)
    category.save()

    assert category.shops.count() == 2
    assert category.shops.filter(name="test_shop1").exists()
    assert category.shops.filter(name="test_shop2").exists()
    assert shop1.categories.count() == 1
    assert shop2.categories.count() == 1
    assert shop1.categories.filter(name="test_category").exists()
    assert shop2.categories.filter(name="test_category").exists()