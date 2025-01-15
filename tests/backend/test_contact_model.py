import django
import pytest

from backend.models import User, Contact


@pytest.mark.django_db
def test_create_contact_default():
    user = User.objects.create_user(email="test_user@test_mail.com")

    contact = Contact.objects.create(user=user)

    assert Contact.objects.count() == 1
    assert contact.user == user
    assert contact.city == ""
    assert contact.street == ""
    assert contact.house == ""
    assert contact.structure == ""
    assert contact.building == ""
    assert contact.apartment == ""
    assert contact.phone == ""
    assert user.contacts.count() == 1
    assert user.contacts.first() == contact


@pytest.mark.django_db
def test_create_contact_special_fields():
    user = User.objects.create_user(email="test_user@test_mail.com")
    city = "test_city"
    street = "test_street"
    house = "test_house"
    structure = "test_structure"
    building = "test_building"
    apartment = "test_apartment"
    phone = "test_phone"

    contact = Contact.objects.create(user=user, city=city, street=street, house=house, structure=structure, building=building, apartment=apartment, phone=phone)

    assert contact.city == city
    assert contact.street == street
    assert contact.house == house
    assert contact.structure == structure
    assert contact.building == building
    assert contact.apartment == apartment
    assert contact.phone == phone


@pytest.mark.django_db
def test_create_contact_without_user():
    with pytest.raises(django.db.utils.IntegrityError):
        Contact.objects.create()