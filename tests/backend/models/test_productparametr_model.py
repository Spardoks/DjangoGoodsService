import django
import pytest

from backend.models import (
    Shop,
    Category,
    Product,
    Parameter,
    ProductParameter,
    ProductInfo,
)


@pytest.mark.django_db
def test_create_productparametr_example():
    category = Category.objects.create(name="test_category")
    product = Product.objects.create(name="test_product", category=category)
    shop = Shop.objects.create(name="test_shop")
    product_info = ProductInfo.objects.create(
        product=product, shop=shop, quantity=10, price=100, price_rrc=200
    )
    parameter = Parameter.objects.create(name="test_parameter")

    product_parameter = ProductParameter.objects.create(
        parameter=parameter, product_info=product_info, value="test_value"
    )

    assert product_parameter.parameter == parameter
    assert product_parameter.product_info == product_info
    assert product_parameter.value == "test_value"
    assert ProductParameter.objects.count() == 1
    assert (
        ProductParameter.objects.get(parameter=parameter, product_info=product_info)
        == product_parameter
    )
    assert product_info.product_parameters.count() == 1
    assert product_info.product_parameters.filter(parameter=parameter).exists()
    assert parameter.product_parameters.count() == 1
    assert parameter.product_parameters.filter(product_info=product_info).exists()
