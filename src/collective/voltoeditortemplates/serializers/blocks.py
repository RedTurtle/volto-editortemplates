from collective.voltoeditortemplates.interfaces import IVoltoEditorTemplatesStore
from plone.restapi.behaviors import IBlocks
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
                return record._attrs.get("config", None)

        return None

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
        block.update({"config": result})

        return block
