import pytest
import yaml

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
    User,
)


def test_read_test_shop_file():
    shop_name = "Связной"
    categories = ["Смартфоны", "Аксессуары", "Flash-накопители", "Телевизоры"]

    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
        assert data["shop"] == shop_name
        assert len(data["categories"]) == 4
        assert len(data["goods"]) == 14
        for category in data["categories"]:
            assert category["name"] in categories


@pytest.mark.django_db
def test_import_test_shop():
    # get data
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
        shop = data["shop"]
        categories = data["categories"]
        goods = data["goods"]

    # define user
    user = User.objects.create_user(email="test_user@test_mail.com", type="shop")

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

    assert Category.objects.count() == len(categories)
    assert Product.objects.count() == len(goods)
    assert ProductInfo.objects.count() == len(goods)
    for item in goods:
        product = Product.objects.filter(id=actual_products_id[item["id"]]).first()
        assert product.name == item["name"]
        assert product.category_id == actual_categories_id[item["category"]]

        product_info = ProductInfo.objects.get(product_id=product.id)
        assert product_info.model == item["model"]
        assert product_info.price == item["price"]
        assert product_info.price_rrc == item["price_rrc"]
        assert product_info.quantity == item["quantity"]
        assert product_info.shop_id == shop.id

        assert product_info.product_parameters.count() == len(item["parameters"])
        for name, value in item["parameters"].items():
            parameter_object = Parameter.objects.filter(name=name).first()
            product_parameter = ProductParameter.objects.filter(
                product_info_id=product_info.id, parameter_id=parameter_object.id
            ).first()
            assert product_parameter.value == str(value)
