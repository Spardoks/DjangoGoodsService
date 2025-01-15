import django
import pytest

from backend.models import User


@pytest.mark.django_db
def test_create_user_default():
    user = User.objects.create_user(email="test@test.com")

    assert user.email == "test@test.com"
    assert user.type == "buyer"
    assert user.is_active == True
    assert user.is_staff == False
    assert user.is_superuser == False

    assert user.first_name == ""
    assert user.last_name == ""
    assert user.company == ""
    assert user.position == ""


@pytest.mark.django_db
def test_create_user_special_type():
    user1 = User.objects.create_user(email="test1@test.com", type="buyer")
    user2 = User.objects.create_user(email="test2@test.com", type="shop")

    assert user1.type == "buyer"
    assert user2.type == "shop"


@pytest.mark.django_db
def test_create_user_unique_emails():
    user1 = User.objects.create_user(email="test1@test.com")

    with pytest.raises(django.db.utils.IntegrityError):
        user2 = User.objects.create_user(email="test1@test.com")


@pytest.mark.django_db
def test_create_superuser_default():
    user = User.objects.create_superuser(email="admin@admin.com", password="admin")

    assert user.email == "admin@admin.com"
    assert user.type == "buyer"
    assert user.is_active == True
    assert user.is_staff == True
    assert user.is_superuser == True

    assert user.first_name == ""
    assert user.last_name == ""
    assert user.company == ""
    assert user.position == ""
