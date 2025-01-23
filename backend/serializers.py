from rest_framework import serializers

from backend.models import (
    Category,
    Contact,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)

##########################################


def import_shop(user, shop_data):
    # ToDo: add format validation
    # ToDo: add user type validation
    try:
        shop = shop_data["shop"]
        categories = shop_data["categories"]
        goods = shop_data["goods"]

        # create shop
        shop, _ = Shop.objects.get_or_create(name=shop, user_id=user.id)

        # create categories
        actual_categories_id = {}
        for category in categories:
            category_object, _ = Category.objects.get_or_create(name=category["name"])
            category_object.shops.add(shop.id)
            category_object.save()
            actual_categories_id[category["id"]] = category_object.id

        # create products, product_infos, parameters and product_parameters
        ProductInfo.objects.filter(shop_id=shop.id).delete()

        actual_products_id = {}
        for item in goods:
            product, _ = Product.objects.get_or_create(
                name=item["name"], category_id=actual_categories_id[item["category"]]
            )
            actual_products_id[item["id"]] = product.id

            product_info = ProductInfo.objects.create(
                product_id=product.id,
                model=item["model"],
                price=item["price"],
                price_rrc=item["price_rrc"],
                quantity=item["quantity"],
                shop_id=shop.id,
            )
            for name, value in item["parameters"].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=value,
                )
    except Exception as e:
        return {"Status": False, "Error": str(e)}

    return {
        "Status": True,
        "actual_products_id": actual_products_id,
        "actual_categories_id": actual_categories_id,
    }


##########################################


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "type"]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
        )


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = (
            "parameter",
            "value",
        )


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = (
            "id",
            "model",
            "product",
            "shop",
            "quantity",
            "price",
            "price_rrc",
            "product_parameters",
        )
        read_only_fields = ("id",)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
            "user",
            "phone",
        )
        read_only_fields = ("id",)
        extra_kwargs = {"user": {"write_only": True}}
