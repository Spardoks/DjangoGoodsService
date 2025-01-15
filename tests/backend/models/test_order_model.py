from datetime import datetime, timezone
import django
import pytest

from backend.models import User, Contact, Order


@pytest.mark.django_db
def test_create_order_default():
    user = User.objects.create_user(email="test_user@test_mail.com")

    order = Order.objects.create(user=user)

    assert Order.objects.count() == 1
    assert order.user == user
    assert order.dt != None
    assert order.contact == None
    assert order.state == ''
    assert user.orders.count() == 1
    assert user.orders.first() == order


@pytest.mark.django_db
def test_create_order_special_fields():
    user1 = User.objects.create_user(email="test_user@test_mail.com")
    user2 = User.objects.create_user(email="test_user2@test_mail.com")
    contact = Contact.objects.create(user=user2)
    dt = datetime.now(timezone.utc)
    state = "new"

    order = Order.objects.create(user=user1, contact=contact, dt=dt, state=state)

    assert order.contact == contact
    assert order.dt == dt
    assert order.state == state


@pytest.mark.django_db
def test_create_order_without_user():
    with pytest.raises(django.db.utils.IntegrityError):
        Order.objects.create()