# -*- coding: utf-8 -*-
from collective.voltoeditortemplates.controlpanel.settings import (
    IVoltoEditorTemplatesSettings,
)
from collective.voltoeditortemplates.controlpanel.settings import (
    IVoltoEditorTemplatesSettingsControlpanel,
)
from plone.restapi.controlpanels import RegistryConfigletPanel
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@adapter(Interface, Interface)
@implementer(IVoltoEditorTemplatesSettingsControlpanel)
class CollectiveVoltoEditorTemplatesSettings(RegistryConfigletPanel):
    schema = IVoltoEditorTemplatesSettings
    configlet_id = "volto-editor-templates-settings"
    configlet_category_id = "Products"
    schema_prefix = None
