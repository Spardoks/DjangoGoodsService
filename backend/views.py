from json import loads as load_json

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import F, Q, Sum
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler
from yaml import Loader
from yaml import load as load_yaml

from backend.models import (
    STATE_CHOICES,
    USER_TYPE_CHOICES,
    Contact,
    Order,
    OrderItem,
    ProductInfo,
    Shop,
    User,
)
from backend.serializers import (
    ContactSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductInfoSerializer,
    ShopSerializer,
    UserSerializer,
    import_shop,
)


# Сейчас используется для 401 Unauthorized приведения к единому виду
# https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and response.status_code == 401:
        data = {"Status": False, "Error": "Пользователь не авторизован"}
        response.status_code = 403
        response.data = data

    return response


###################################################


# For testing
@api_view(["GET"])
def test_ping_view(request):
    return Response({"Status": True}, status=200)


# For testing
@api_view(["GET"])
def test_user_list(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response({"Status": True, "users": serializer.data}, status=200)


# For testing
@api_view(["POST"])
def test_do_authorized_action(request):
    if not request.user.is_authenticated:
        return Response(
            {"Status": False, "Error": "Пользователь не опознан"}, status=403
        )
    return Response({"Status": True}, status=200)


###################################################


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
    if request.user.is_authenticated:
        return Response(
            {"Status": False, "Error": "Пользователь уже авторизован"}, status=403
        )

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


# ToDo
@api_view(["POST"])
def logout_user(request):
    if not request.user.is_authenticated:
        return Response(
            {"Status": False, "Error": "Пользователь не опознан"}, status=403
        )
    request.user.auth_token.delete()
    return Response({"Status": True}, status=200)


# ToDo: other error message when exception
@api_view(["GET"])
def list_products(request):
    try:
        query = Q(shop__state=True)
        shop_id = request.query_params.get("shop_id")
        category_id = request.query_params.get("category_id")

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = (
            ProductInfo.objects.filter(query)
            .select_related("shop", "product__category")
            .prefetch_related("product_parameters__parameter")
            .distinct()
        )
        serializer = ProductInfoSerializer(queryset, many=True)
    except Exception as e:
        return Response({"Status": False, "Error": str(e)}, status=403)

    return Response({"Status": True, "products": serializer.data}, status=200)


class ContactView(APIView):

    # получить мои контакты
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response({"Status": True, "contacts": serializer.data}, status=200)

    # добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        if {"city", "street", "phone"}.issubset(request.data):
            request.data._mutable = True
            request.data.update({"user": request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True}, status=200)
            else:
                return Response(
                    {"Status": False, "Error": serializer.errors}, status=403
                )

        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )

    # удалить контакт
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        items_sting = request.data.get("items")
        if items_sting:
            items_list = items_sting.split(",")
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return Response({"Status": True, "deleted": deleted_count}, status=200)
        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )

    # редактировать контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        if "id" in request.data:
            if request.data["id"].isdigit():
                contact = Contact.objects.filter(
                    id=request.data["id"], user_id=request.user.id
                ).first()
                if contact:
                    serializer = ContactSerializer(
                        contact, data=request.data, partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()
                        return Response({"Status": True}, status=200)
                    else:
                        return Response(
                            {"Status": False, "Error": serializer.errors}, status=403
                        )

        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )


# ToDo: add delete orders if no order_items
# ToDo: add errors if order status is not basket
class BasketView(APIView):

    # получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )
        basket = (
            Order.objects.filter(user_id=request.user.id, state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
        )

        serializer = OrderSerializer(basket, many=True)
        return Response({"Status": True, "orders": serializer.data}, status=200)

    # добавить товары в корзину
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        items_sting = request.data.get("items")
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return Response(
                    {"Status": False, "Error": "Неверный формат запроса"}, status=403
                )
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, state="basket"
                )
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({"order": basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return Response(
                                {"Status": False, "Error": str(error)}, status=403
                            )
                        else:
                            objects_created += 1
                    else:
                        return Response(
                            {"Status": False, "Error": serializer.errors}, status=403
                        )

                return Response(
                    {"Status": True, "created": objects_created}, status=200
                )
        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        items_sting = request.data.get("items")
        if items_sting:
            items_list = items_sting.split(",")
            basket, _ = Order.objects.get_or_create(
                user_id=request.user.id, state="basket"
            )
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return Response({"Status": True, "deleted": deleted_count}, status=200)
        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )

    # обновить позиции в корзине
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        items_sting = request.data.get("items")
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return Response(
                    {"Status": False, "Error": "Неверный формат запроса"}, status=403
                )
            else:
                basket, _ = Order.objects.get_or_create(
                    user_id=request.user.id, state="basket"
                )
                objects_updated = 0
                for order_item in items_dict:
                    if (
                        type(order_item["order_item_id"]) == int
                        and type(order_item["quantity"]) == int
                    ):
                        objects_updated += OrderItem.objects.filter(
                            order_id=basket.id, id=order_item["order_item_id"]
                        ).update(quantity=order_item["quantity"])

                return Response(
                    {"Status": True, "updated": objects_updated}, status=200
                )
        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )
        order = (
            Order.objects.filter(user_id=request.user.id)
            .exclude(state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
        )

        serializer = OrderSerializer(order, many=True)
        return Response({"Status": True, "orders": serializer.data}, status=200)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        if {"basket_id", "contact_id"}.issubset(request.data):
            if request.data["basket_id"].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id,
                        id=request.data["basket_id"],
                        state="basket",
                    ).update(contact_id=request.data["contact_id"], state="new")
                except IntegrityError as error:
                    print(error)
                    return Response(
                        {"Status": False, "Error": "Неправильно указаны аргументы"},
                        status=403,
                    )
                else:
                    if is_updated:
                        # ToDo: вероятно, будет корректнее,
                        # если исходную карзину удалить,
                        # создать на каждый OrderItem в корзине отдельный заказ со статусом new
                        # для правильной работы по оповещениям, изменениям статусов и отслеживаниям
                        # ToDo: отправить уведомление магазину о новом заказе
                        return Response({"Status": True}, status=200)

        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )


class PartnerOrderView(APIView):
    """
    Класс для получения и изменения статуса заказов пользователями
    """

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        if request.user.type != "shop":
            return Response(
                {"Status": False, "Error": "Только для магазинов"}, status=403
            )

        order = (
            Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id
            )
            .exclude(state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .annotate(
                total_sum=Sum(
                    F("ordered_items__quantity")
                    * F("ordered_items__product_info__price")
                )
            )
            .distinct()
        )

        serializer = OrderSerializer(order, many=True)
        return Response({"Status": True, "orders": serializer.data}, status=200)

    # обновить статус заказа
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {"Status": False, "Error": "Нужно быть залогиненным"}, status=403
            )

        if request.user.type != "shop":
            return Response(
                {"Status": False, "Error": "Только для магазинов"}, status=403
            )

        if {"order_id", "state"}.issubset(request.data):
            correct_states = [
                state[0] for state in STATE_CHOICES if state[0] != "basket"
            ]
            if request.data["state"] not in correct_states:
                return Response(
                    {"Status": False, "Error": "Неправильно указаны аргументы"},
                    status=403,
                )
            if request.data["order_id"].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        ordered_items__product_info__shop__user_id=request.user.id,
                        id=request.data["order_id"],
                    ).update(
                        state=request.data["state"],
                    )
                except IntegrityError as error:
                    print(error)
                    return Response(
                        {"Status": False, "Error": "Неправильно указаны аргументы"},
                        status=403,
                    )
                else:
                    if is_updated:
                        # ToDo: отправить уведомление пользователю об изменении статуса
                        return Response({"Status": True}, status=200)

        return Response(
            {"Status": False, "Error": "Не указаны все необходимые аргументы"},
            status=403,
        )


@api_view(["GET"])
def list_shops(request):
    try:
        query = Q(state=True)
        id = request.query_params.get("shop_id")

        if id:
            query = query & Q(id=id)

        queryset = Shop.objects.filter(query)
        serializer = ShopSerializer(queryset, many=True)
    except Exception as e:
        return Response({"Status": False, "Error": str(e)}, status=403)
    return Response({"Status": True, "shops": serializer.data}, status=200)
