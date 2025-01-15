import django
import pytest

from backend.models import User, Shop


@pytest.mark.django_db
def test_create_shop_default():
    user = User.objects.create_user(email="test_user@test_mail.com")
    shop_name = "test_shop"

    shop = Shop.objects.create(name=shop_name, user=user)

    assert Shop.objects.count() == 1
    assert Shop.objects.get(name=shop_name) == shop
    assert shop.name == shop_name
    assert shop.user == user
    assert shop.url == None
    assert shop.state == True

@pytest.mark.django_db
def test_create_shop_custom_fields():
    user = User.objects.create_user(email="test_user@test_mail.com")
    shop_name = "test_shop"
    shop_url = "https://test_shop.com"
    shop_state = True

    shop = Shop.objects.create(name=shop_name, url=shop_url, user=user, state=shop_state)

    assert shop.name == shop_name
    assert shop.user == user
    assert shop.url == shop_url
    assert shop.state == shop_state


@pytest.mark.django_db
def test_create_shop_no_user():
    shop_name = "test_shop"

    shop = Shop.objects.create(name=shop_name)

    assert shop.user == None


@pytest.mark.django_db
def test_create_shop_and_add_existing_user():
    user = User.objects.create_user(email="test_user@test_mail.com")
    shop_name = "test_shop"
    shop = Shop.objects.create(name=shop_name)

    shop.user = user
    shop.save()

    assert shop.user == user


@pytest.mark.django_db
def test_create_shop_and_add_non_existing_user():
    user = User(email="test_user@test_mail.com")
    shop_name = "test_shop"
    shop = Shop.objects.create(name=shop_name)

    shop.user = user

    with pytest.raises(ValueError):
        shop.save()


@pytest.mark.django_db
def test_cascade_delete_shop_after_user_is_deleted():
    user = User.objects.create_user(email="test_user@test_mail.com")
    shop_name = "test_shop"
    Shop.objects.create(name=shop_name, user=user)

    user.delete()

    with pytest.raises(Shop.DoesNotExist):
        Shop.objects.get(name=shop_name)