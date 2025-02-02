import pytest
from aiosmtpd.controller import Controller
from django.conf import settings
from django.core import mail
from django.core.mail import send_mail

FROM_ADDRESS_HANDLER_GOT = None
MESSAGE_HANDLER_GOT = None
TO_ADDRESS_HANDLER_GOT = None


# https://aiosmtpd-pepoluan.readthedocs.io/en/latest/controller.html
class DjangoTestMessageAiosmtpdHandler:
    async def handle_DATA(self, server, session, envelope):
        print()
        print(
            "Messge: ",
            envelope.content.decode("utf8", errors="replace").splitlines(),
            end="",
        )
        print("\nFrom: ", envelope.mail_from, end="")
        print("\nTo: ", envelope.rcpt_tos, end="")
        print()

        global FROM_ADDRESS_HANDLER_GOT
        FROM_ADDRESS_HANDLER_GOT = envelope.mail_from
        global MESSAGE_HANDLER_GOT
        MESSAGE_HANDLER_GOT = envelope.content.decode(
            "utf8", errors="replace"
        ).splitlines()[-1]
        global TO_ADDRESS_HANDLER_GOT
        TO_ADDRESS_HANDLER_GOT = envelope.rcpt_tos

        return "250 Message accepted for delivery"


# smtp test backend
@pytest.mark.django_db
def test_django_send_email_locmem():
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    send_mail(
        subject="Test Subject",
        message="Test Message",
        from_email="from@example.com",
        recipient_list=["to@example.com"],
    )

    # Проверка, что письмо было отправлено
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test Subject"
    assert mail.outbox[0].body == "Test Message"
    assert mail.outbox[0].from_email == "from@example.com"
    assert mail.outbox[0].to == ["to@example.com"]


# real smtp integration test
@pytest.mark.django_db
def test_django_send_email_aiosmtpd():
    EMAIL_HOST = "localhost"  # for testing - aiosmtpd
    EMAIL_PORT = 8025
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False

    controller = Controller(
        hostname=EMAIL_HOST, port=EMAIL_PORT, handler=DjangoTestMessageAiosmtpdHandler()
    )
    controller.start()

    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    settings.EMAIL_HOST = EMAIL_HOST
    settings.EMAIL_PORT = EMAIL_PORT
    settings.EMAIL_HOST_USER = EMAIL_HOST_USER
    settings.EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
    settings.EMAIL_USE_TLS = EMAIL_USE_TLS
    settings.EMAIL_USE_SSL = EMAIL_USE_SSL

    subject = "subject"
    message = "Test message"
    from_email = "shop@test.com"
    to_emails = ["buyer@test.com"]
    result_send_mail = send_mail(subject, message, from_email, to_emails)

    assert result_send_mail == 1
    assert FROM_ADDRESS_HANDLER_GOT == from_email
    assert TO_ADDRESS_HANDLER_GOT == to_emails
    assert MESSAGE_HANDLER_GOT == message
