from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

from backend.models import ConfirmEmailToken, User

new_order = Signal(
    # providing_args=["user_id"],
)

new_user_registered = Signal(
    # providing_args=['user_id'],
)


# ToDo: разделить логику для пользователя и магазина
@receiver(new_order)
def new_order_signal(user_id, order_id, **kwargs):
    """
    отправяем письмо при изменении статуса заказа
    """
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Обновление статуса/создание заказа",
        # message:
        f"Смотрите заказ {order_id}",
        # from:
        settings.EMAIL_HOST_USER,  # notificator email
        # to:
        [user.email],
    )
    msg.send()


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email],
    )
    msg.send()
