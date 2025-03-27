from copy import deepcopy

from AccessControl import Unauthorized
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.batching import HypermediaBatch
from plone.restapi.blocks import iter_block_transform_handlers
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import (
    IBlockFieldDeserializationTransformer,
    IBlockFieldSerializationTransformer,
)
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.services import Service
from zExceptions import BadRequest, NotFound
from zope.component import getUtility
from zope.interface import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from collective.voltoeditortemplates.interfaces import IVoltoEditorTemplatesStore

DEFAULT_SORT_KEY = "name"


class BlocksTemplatesService(Service):
    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []
        self.store = IVoltoEditorTemplatesStore

    def can_delete_templates(self):
        return api.user.has_permission(
            "collective.voltoeditortemplates: Delete Templates"
        )

    def deserialize_blocks(self, blocks):
        for block in blocks.values():
            new_block = block.copy()
            for handler in iter_block_transform_handlers(
                self.context, block, IBlockFieldDeserializationTransformer
            ):
                new_block = handler(new_block)
                print(new_block)
            block.clear()
            block.update(new_block)

        return blocks

    def serialize_blocks(self, blocks):
        results = {}

        for key, block in blocks.items():
            new_block = deepcopy(block)
            handlers = iter_block_transform_handlers(
                self.context,
                block,
                IBlockFieldSerializationTransformer,
            )
            for h in handlers:
                new_block = h(new_block)
            results[key] = new_block

        return results


class AddBlockTemplate(BlocksTemplatesService):
    """Crea un nuovo template"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def validate_form(self, form_data):
        """
        check all required fields and parameters
        """
        for field in ["id", "config"]:
            value = form_data.get(field, "")
            if not value:
                raise BadRequest(f"Campo obbligatorio mancante: {field}")

    def reply(self):
        alsoProvides(
            self.request, IDisableCSRFProtection
        )  # Disabilita il controllo CSRF

        json_data = json_body(self.request)
        store = getUtility(self.store)
        try:
            res = store.add(json_data)
        except ValueError as e:
            self.request.response.setStatus(500)
            return dict(
                error=dict(
                    type="InternalServerError",
                    message=getattr(e, "message", e.__str__()),
                )
            )

        if res:
            return self.reply_no_content()

        self.request.response.setStatus(500)
        return dict(
            error=dict(
                type="InternalServerError",
                message="Unable to add. Contact site manager.",
            )
        )


@implementer(IPublishTraverse)
class GetBlockTemplates(BlocksTemplatesService):
    """Recupera la lista di tutti i template,
    con possibilità di ricerca per titolo"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def publishTraverse(self, request, uid):
        # Consume any path segments after /@users as parameters
        self.params.append(uid)
        return self

    def reply(self):
        if self.params:
            # single object detail
            results = self.get_template(self.params[0])
        else:
            results = self.get_available_templates()

        batch = HypermediaBatch(self.request, results)
        data = {
            "@id": batch.canonical_url,
            "items": [self.fix_fields(data=x) for x in batch],
            "items_total": batch.items_total,
        }
        links = batch.links
        if links:
            data["batching"] = links

        data["actions"] = {"can_delete_templates": self.can_delete_templates()}
        return data

    def get_template(self, uid):
        tool = getUtility(IVoltoEditorTemplatesStore)
        blocks = [
            {
                "id": record._attrs.get("id", ""),
                "date": record._attrs.get("date", ""),
                "config": self.serialize_blocks(
                    deepcopy(record._attrs.get("config", "").get("blocks", {}))
                ),
                # "config": record._attrs.get("config", ""),
                "name": record._attrs.get("name", ""),
                "uid": record.intid,
            }
            for record in tool.search()
            if record.intid == int(uid)
        ]
        return blocks

    def fix_fields(self, data):
        """
        Make data json compatible
        """
        for k, v in data.items():
            data[k] = json_compatible(v)
        return data

    def parse_query(self):
        query = deepcopy(self.request.form)
        query = unflatten_dotted_dict(query)
        res = {}
        res["query"] = query
        return res

    def get_single_object_template(self, search_value):
        """
        Return data for single object
        """
        results = []
        tool = getUtility(self.store)
        results = tool.search(query={"name": search_value})
        name = search_value

        if not results:
            return results

        templates = []

        for record in results:
            config = deepcopy(record._attrs.get("config", ""))
            original_blocks = config.get("blocks", {})
            serialized_blocks = self.serialize_blocks(original_blocks)

            config_blocks = {
                key: serialized_blocks.get(key, value)
                for key, value in original_blocks.items()
            }

            templates.append(
                {
                    "id": record._attrs.get("id", ""),
                    "date": record._attrs.get("date", ""),
                    "config": {
                        **record.a.get("config", {}),
                        "blocks": config_blocks,
                    },
                    "name": name,
                    "uid": record.intid,
                }
            )

        return templates

    def sort_result(self, result):
        return sorted(result, key=lambda x: x[DEFAULT_SORT_KEY])

    def get_available_templates(self):
        tool = getUtility(IVoltoEditorTemplatesStore)
        templates = {}

        query = unflatten_dotted_dict(self.request.form)
        text = query.get("name", "")
        if text:
            query_res = tool.search(query={"name": f"{text}*"})
        else:
            query_res = tool.search()

        for template in query_res:
            uid = template.intid

            if uid not in templates:
                new_data = {
                    "config": template._attrs.get(
                        "config", {"blocks": [], "blocks_layout": []}
                    ),
                    "date": template._attrs.get("date", None),
                    "name": template._attrs.get("name", ""),
                    "id": template._attrs.get("id", ""),
                    "uid": uid,
                }

                templates[uid] = new_data

        result = []

        for res in list(templates.values()):
            original_blocks = res.get("config", {}).get("blocks", {})
            serialized_blocks = self.serialize_blocks(original_blocks)

            config_blocks = {
                key: serialized_blocks.get(key, value)
                for key, value in original_blocks.items()
            }

            result.append(
                {
                    **res,
                    "config": {
                        **res.get("config", {}),
                        "blocks": config_blocks,
                    },
                }
            )

        return self.sort_result(result)


class UpdateBlockTemplate(BlocksTemplatesService):
    """Aggiorna un template"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def reply(self):
        alsoProvides(self.request, IDisableCSRFProtection)

        json_data = json_body(self.request)
        template_id = json_data.get("uid", None)
        if not template_id:
            raise NotFound("Template not found")
        store = getUtility(self.store)

        # Apply deserialization to the incoming template data
        original_blocks = json_data.get("config", {}).get("blocks", {})
        deserialized_blocks = self.deserialize_blocks(original_blocks)
        json_data["config"]["blocks"] = deserialized_blocks

        result = store.update(template_id, json_data)
        if result is None:
            return self.reply_no_content()
        self.request.response.setStatus(500)

        return dict(
            error=dict(
                type="InternalServerError",
                message="Unable to update template. Contact site manager.",
            )
        )


class DeleteBlockTemplate(BlocksTemplatesService):
    """Elimina un template"""

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params = []

    def reply(self):
        if not self.can_delete_templates():
            raise Unauthorized(
                "Non hai i permessi necessari per eseguire questa azione."
            )
        alsoProvides(self.request, IDisableCSRFProtection)
        json_data = json_body(self.request)
        template_id = json_data.get("uid", None)
        if not template_id:
            raise NotFound("Template not found")
        store = getUtility(self.store)
        result = store.delete(template_id)
        if result is None:
            return self.reply_no_content()
        if "error" in result:
            raise NotFound("Template not found")
        self.request.response.setStatus(500)
