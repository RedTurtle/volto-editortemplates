from collective.voltoeditortemplates.interfaces import IVoltoEditorTemplatesStore
from collective.voltoeditortemplates.serializers.blocks import BlockTemplateSerializer
from plone.restapi.behaviors import IBlocks
from unittest.mock import Mock
from unittest.mock import patch
from zope.component import provideUtility
from zope.publisher.interfaces.browser import IBrowserRequest

import pytest


@pytest.fixture
def mock_store():
    """Mock of store template"""
    store = Mock(spec=IVoltoEditorTemplatesStore)
    record_mock = Mock()
    record_mock.intid = 123
    record_mock._attrs = {"config": {"some": "config"}}
    store.search = Mock(
        return_value=[record_mock]
    )  # !!!Definisci esplicitamente search

    # !!!Registra il mock come utility Zope
    provideUtility(store, IVoltoEditorTemplatesStore)

    return store


@pytest.fixture
def mock_context():
    return Mock(spec=IBlocks)


@pytest.fixture
def mock_request():
    return Mock(spec=IBrowserRequest)


def test_block_serializer_valid_uid(mock_context, mock_request, mock_store):
    """Test block serializer with valid uid"""
    with patch("zope.component.getUtility", return_value=mock_store):
        serializer = BlockTemplateSerializer(mock_context, mock_request)
        block = {"uid": 123}
        result = serializer(block)

        assert "config" in result
        assert result["config"] == {"some": "config"}


def test_block_serializer_missing_uid(mock_context, mock_request):
    """Test block serializer with missing uid"""
    serializer = BlockTemplateSerializer(mock_context, mock_request)
    block = {}

    result = serializer(block)

    assert "error" in result
    assert result["error"]["type"] == "InternalServerError"
    assert result["error"]["code"] == "VOLTO_EDITOR_TEMPLATES_INVALID"


def test_block_serializer_invalid_uid(mock_context, mock_request, mock_store):
    """Test block serializer with invalid uid"""
    with patch("zope.component.getUtility", return_value=mock_store):
        serializer = BlockTemplateSerializer(mock_context, mock_request)
        block = {"uid": 999}  # UID non esistente
        result = serializer(block)

        assert "error" in result
        assert result["error"]["code"] == "VOLTO_EDITOR_TEMPLATES_NO_TEMPLATE"
