import pytest


@pytest.fixture()
def portal(functional):
    portal = functional["portal"]

    yield portal


@pytest.fixture()
def http_request(functional):
    return functional["request"]
