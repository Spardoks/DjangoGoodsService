from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from requests import get
from rest_framework.decorators import api_view
from rest_framework.response import Response
from yaml import Loader
from yaml import load as load_yaml

from backend.models import User
from backend.serializers import UserSerializer, import_shop


@api_view(["GET"])
def ping_view(request):
    return Response({"status": "OK"})


@api_view(["GET"])
def user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


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
