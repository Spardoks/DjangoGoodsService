from datetime import datetime, timezone

import django
import pytest

from backend.models import ConfirmEmailToken, User


@pytest.mark.django_db
def test_create_token_without_user():
    with pytest.raises(django.db.utils.IntegrityError):
        ConfirmEmailToken.objects.create()


@pytest.mark.django_db
def test_create_token_with_user():
    user = User.objects.create_user(email="test_user@test_mail.com")
    dt = datetime.now(timezone.utc)

    token = ConfirmEmailToken.objects.create(user=user, created_at=dt)
    assert ConfirmEmailToken.objects.count() == 1
    assert ConfirmEmailToken.objects.filter(user=user).exists()

    assert token.key is not None
    assert len(token.key) <= 64
    assert len(token.key) >= 1

    assert token.created_at.year == dt.year
    assert token.created_at.month == dt.month
    assert token.created_at.day == dt.day
    assert token.created_at.hour == dt.hour
    assert token.created_at.minute == dt.minute
    assert token.created_at.second == dt.second
