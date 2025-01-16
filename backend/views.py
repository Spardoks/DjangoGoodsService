from requests import get
from rest_framework.decorators import api_view
from rest_framework.response import Response
from yaml import Loader
from yaml import load as load_yaml

from backend.models import User
from backend.serializers import UserSerializer


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
    url = request.data.get("url")
    user = request.data.get("user")

    stream = get(url).content
    data = load_yaml(stream, Loader=Loader)

    print(data)

    return Response({"url": url, "user": user, "data": data})
