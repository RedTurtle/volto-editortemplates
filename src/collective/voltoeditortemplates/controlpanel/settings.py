# -*- coding: utf-8 -*-
from collective.voltoeditortemplates import _
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.restapi.controlpanels.interfaces import IControlpanel
from zope.interface import Interface


class IVoltoEditorTemplatesSettingsControlpanel(IControlpanel):
    """ """


class IVoltoEditorTemplatesSettings(Interface):
    """"""


class VoltoEditorTemplatesControlPanelForm(RegistryEditForm):
    schema = IVoltoEditorTemplatesSettings
    id = "volto-editor-templates-settings"
    label = _("Editor templates")


class VoltoEditorTemplatesControlPanelView(ControlPanelFormWrapper):
    """ """

    form = VoltoEditorTemplatesControlPanelForm
