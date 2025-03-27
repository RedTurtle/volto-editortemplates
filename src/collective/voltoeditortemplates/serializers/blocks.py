from collective.voltoeditortemplates.interfaces import IVoltoEditorTemplatesStore
from copy import deepcopy
from plone.restapi.behaviors import IBlocks
from plone.restapi.blocks import iter_block_transform_handlers
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class BlockTemplateSerializer:
    order = 0
    block_type = "blockTemplateSelector"

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.store = IVoltoEditorTemplatesStore

    def get_template(self, uid):
        tool = getUtility(IVoltoEditorTemplatesStore)
        for record in tool.search():
            if record.intid == int(uid):
                soup_record_config = record._attrs.get("config", None)
                return deepcopy(soup_record_config)
        return None

    def serialize(self, blocks):
        """
        blocks: dizionario dei blocchi da trasformare. sarà sempre uno.
        """
        results = {}
        for key, block in blocks.items():
            new_block = deepcopy(block)  # Copia profonda per evitare riferimenti
            handlers = iter_block_transform_handlers(
                self.context,
                block,
                IBlockFieldSerializationTransformer,
            )
            for h in handlers:
                new_block = h(new_block)
            results[key] = new_block

        return results

    def __call__(self, block):
        if not block.get("uid", None):
            block.update(
                {
                    "@type": "blockTemplateSelector",
                    "error": {
                        "type": "InternalServerError",
                        "message": "Unable to get block config for template.",  # noqa
                        "code": "VOLTO_EDITOR_TEMPLATES_INVALID",
                    },
                }
            )
            return block

        result = self.get_template(block.get("uid"))

        if not result:
            block.update(
                {
                    "@type": "blockTemplateSelector",
                    "error": {
                        "type": "InternalServerError",
                        "message": "Unable to get block template.",  # noqa
                        "code": "VOLTO_EDITOR_TEMPLATES_NO_TEMPLATE",
                    },
                }
            )
            return block
        # block_data = list(result.get("blocks").values())[0]
        # handlers = iter_block_transform_handlers(
        #     self.context,
        #     block_data,
        #     IBlockFieldSerializationTransformer,
        # )

        # for h in handlers:
        #     result = h(block_data)
        # passiamo soltanto i blocchi che dobbiamo 'ripassare'
        result = self.serialize(result.get("blocks"))
        block.update({"config": result})

        return block
