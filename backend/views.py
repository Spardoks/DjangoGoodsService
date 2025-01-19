from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from yaml import Loader
from yaml import load as load_yaml

from backend.models import USER_TYPE_CHOICES, User
from backend.serializers import UserSerializer, import_shop


# ToDo: сделать ответ по спецификации
@api_view(["GET"])
def ping_view(request):
    return Response({"status": "OK"})


# ToDo: сделать ответ по спецификации
@api_view(["GET"])
def user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


# ToDo: сделать ответ по спецификации
@api_view(["POST"])
def update_shop(request):
    # check user
    user_email = request.data.get("user")
    if user_email is None:
        return Response(
            {"Status": False, "Error": "Не указан emeil пользователя"}, status=403
        )
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return Response(
            {"Status": False, "Error": "Пользователь не найден"}, status=403
        )
    if user.type != "shop":
        return Response(
            {"Status": False, "Error": "Пользователь должен быть владельцем магазина"},
            status=403,
        )

    # check url
    data_url = request.data.get("url")
    if data_url is None:
        return Response(
            {"Status": False, "Error": "Не указан url данных для загрузки"}, status=403
        )
    validate_url = URLValidator()
    try:
        validate_url(data_url)
    except ValidationError as e:
        return Response({"Status": False, "Error": "Некорректный url"}, status=403)

    # get data
    try:
        stream = get(data_url).content
    except Exception as e:
        return Response(
            {"Status": False, "Error": "Возникла ошибка при запросе данных"}, status=403
        )
    try:
        data = load_yaml(stream, Loader=Loader)
    except Exception as e:
        return Response(
            {
                "Status": False,
                "Error": "Данные не соответствуют требованиям по формату",
            },
            status=403,
        )

    # save data
    result = import_shop(user, data)
    result["url"] = data_url
    result["user"] = user_email
    result["data"] = data
    status = 200 if result["Status"] else 403

    return Response(result, status=status)


# ToDo: сделать ответ по спецификации
# ToDo: сделать корректное логирование
# ToDo: задание строк единообразно
# ToDo: разделение логина для админа и пользователя
# ToDo: сделать сброс пароля
@api_view(["POST"])
def register_user(request):
    # check mail
    user_email = request.data.get("email")
    if user_email is None:
        print("Не указан emeil пользователя")
        return Response(
            {"Status": False, "Error": "Не указан emeil пользователя"}, status=403
        )
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        pass
    else:
        print("Пользователь уже существует")
        return Response(
            {"Status": False, "Error": "Пользователь уже существует"}, status=403
        )

    # check type
    user_type = request.data.get("type")
    if user_type not in [
        USER_TYPE_CHOICES[i][0] for i in range(len(USER_TYPE_CHOICES))
    ]:
        print("Неверный тип пользователя")
        return Response(
            {"Status": False, "Error": "Неверный тип пользователя"},
            status=403,
        )

    # check password
    user_password = request.data.get("password")
    if user_password is None:
        print("Не указан пароль пользователя")
        return Response(
            {"Status": False, "Error": "Не указан пароль пользователя"},
            status=403,
        )

    # create user
    try:
        user = User.objects.create_user(
            email=user_email, password=user_password, type=user_type
        )
    except Exception:
        print("Возникла ошибка при регистрации пользователя")
        return Response(
            {"Status": False, "Error": "Возникла ошибка при регистрации пользователя"},
            status=403,
        )

    return Response({"Status": True}, status=200)


# ToDo: сделать ответ по спецификации
# ToDo: сделать получение токена более безопасным
# ToDo: также попробовать POST-запрос на api-token-auth с именем пользователя и паролем
@api_view(["POST"])
def login_user(request):
    user_email = request.data.get("email")
    user_password = request.data.get("password")

    user = User.objects.filter(email=user_email).first()
    if user is None:
        return Response(
            {"Status": False, "Error": "Пользователь не найден"}, status=403
        )

    if not user.check_password(user_password):
        return Response({"Status": False, "Error": "Неверный пароль"}, status=403)

    token, created = Token.objects.get_or_create(user=user)
    if not created:
        return Response(
            {"Status": False, "Error": "Не удалось создать токен"}, status=403
        )

    return Response({"Status": True, "token": str(token)}, status=200)


@api_view(["POST"])
def do_authorized_action(request):
    if not request.user.is_authenticated:
        return Response(
            {"Status": False, "Error": "Пользователь не авторизован"}, status=403
        )
    return Response({"Status": True}, status=200)


# ToDo
# @api_view(["POST"])
# def logout_user(request):
#     if not request.user.is_authenticated:
#         return Response(
#             {"Status": False, "Error": "Пользователь не авторизован"}, status=403
#         )
#     request.user.auth_token.delete()
#     return Response({"Status": True}, status=200)
