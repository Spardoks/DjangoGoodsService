from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

from backend.models import User

new_order = Signal(
    # providing_args=["user_id"],
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
