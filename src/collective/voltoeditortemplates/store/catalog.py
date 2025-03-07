# -*- coding: utf-8 -*-
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from souper.soup import NodeTextIndexer
from zope.interface import implementer


@implementer(ICatalogFactory)
class VoltoEditorTemplatesCatalogFactory(object):
    def __call__(self, context):
        catalog = Catalog()

        text_indexer = NodeTextIndexer(["name"])
        catalog["name"] = CatalogTextIndex(text_indexer)

        uid_indexer = NodeAttributeIndexer("uid")
        catalog["uid"] = CatalogFieldIndex(uid_indexer)

        return catalog
