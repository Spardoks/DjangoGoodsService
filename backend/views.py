from rest_framework.decorators import api_view
from rest_framework.response import Response


from backend.models import User
from backend.serializers import UserSerializer


@api_view(['GET'])
def ping_view(request):
    return Response({"status": "OK"})


@api_view(["GET"])
def user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)
