import django
import pytest

from backend.models import Parameter


@pytest.mark.django_db
def test_create_parameter_example():
    parameter_name = "test_parameter"

    parameter = Parameter.objects.create(name=parameter_name)

    assert parameter.name == parameter_name
    assert Parameter.objects.count() == 1
    assert Parameter.objects.get(name=parameter_name) == parameter