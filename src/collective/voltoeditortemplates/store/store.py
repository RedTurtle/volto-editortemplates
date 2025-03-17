# -*- coding: utf-8 -*-
from datetime import datetime
from plone import api
from repoze.catalog.query import And, Any, Eq, Contains
from souper.soup import get_soup, Record
from zope.interface import implementer
from collective.voltoeditortemplates.interfaces import (
    IVoltoEditorTemplatesStore,
)
import logging
import uuid

logger = logging.getLogger(__name__)


@implementer(IVoltoEditorTemplatesStore)
class VoltoEditorTemplatesStore(object):
    """Gestisce i template dei blocchi salvati in Soup"""

    fields = ["id", "name", "config", "date"]
    text_index = "name"
    indexes = ["name", "id"]
    keyword_indexes = []

    @property
    def soup(self):
        """Ritorna il Soup per i template"""
        return get_soup("volto_editor_templates_soup", api.portal.get())

    def add(self, data):
        """Aggiunge un nuovo template"""
        record = Record()
        record.attrs["id"] = str(uuid.uuid4())  # Genera un ID univoco
        record.attrs["date"] = datetime.now()

        for k, v in data.items():
            if k not in self.fields:
                logger.debug(f"[ADD] SKIP campo sconosciuto: {k}")
                continue
            record.attrs[k] = v

        self.soup.add(record)
        self.soup.reindex()
        return record.attrs["id"]

    def get(self, template_id):
        """Recupera un template dato il suo ID"""
        records = [r for r in self.soup.query() if r.attrs.get("id") == template_id]
        return records[0].attrs if records else None

    def update(self, template_id, data):
        """Aggiorna un template esistente"""
        try:
            record = self.soup.get(template_id)
        except KeyError:
            logger.error('[UPDATE] item with id "{}" not found.'.format(template_id))
            return {"error": "NotFound"}
        for k, v in data.items():
            if k not in self.fields:
                logger.debug("[UPDATE] SKIP unkwnown field: {}".format(k))

            else:
                record.attrs[k] = v

        self.soup.reindex(records=[record])

    def delete(self, template_id):
        """Elimina un template"""
        record = self.soup.get(template_id)
        if not record:
            logger.error(f"[DELETE] Template con id {template_id} non trovato.")
            return {"error": "NotFound"}

        del self.soup[record]
        self.soup.reindex()

    def search(self, query=None, sort_index="name", reverse=True):
        """Cerca template per nome o ID"""
        queries = []
        if query:
            queries = [
                self.parse_query_params(index, value)
                for index, value in query.items()
                if index in self.indexes and value
            ]
        if queries:
            return [
                x
                for x in self.soup.query(
                    And(*queries), sort_index=sort_index, reverse=reverse
                )
            ]

        # Restituisci tutti i dati
        records = self.soup.data.values()
        return sorted(
            records, key=lambda k: k.attrs.get(sort_index, ""), reverse=reverse
        )

    def parse_query_params(self, index, value):
        """Parser per i filtri di ricerca"""
        if index == self.text_index:
            return Contains(self.text_index, value)
        elif index in self.keyword_indexes:
            return Any(index, value)
        else:
            return Eq(index, value)

    def clear(self):
        """Svuota completamente il database dei template"""
        self.soup.clear()
