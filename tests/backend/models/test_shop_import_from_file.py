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

from backend.serializers import import_shop

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
    assert Shop.objects.count() == 0
    assert User.objects.count() == 0

    # define user
    user = User.objects.create_user(email="test_user@test_mail.com", type="shop")
    assert User.objects.count() == 1

    # get data
    with open("tests/backend/models/test_shop.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(
            f,
        )
    result = import_shop(user, data)
    assert "Status" in result
    assert "actual_categories_id" in result
    assert "actual_products_id" in result
    assert result["Status"] == True

    assert User.objects.count() == 1
    assert Shop.objects.count() == 1
    shop_by_user = Shop.objects.filter(user_id=user.id).first()
    shop_by_name = Shop.objects.filter(name=data["shop"]).first()
    assert shop_by_user == shop_by_name

    actual_categories_id = result["actual_categories_id"]
    actual_products_id = result["actual_products_id"]
    categories = data["categories"]
    goods = data["goods"]

    assert len(actual_categories_id) == len(categories)
    assert len(actual_products_id) == len(goods)
    assert Category.objects.count() == len(categories)
    assert Product.objects.count() == len(goods)
    assert ProductInfo.objects.count() == len(goods)
    shop = shop_by_name
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
