from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IVoltoEditorTemplatesLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IVoltoEditorTemplatesStore(Interface):
    """Marker interface"""
