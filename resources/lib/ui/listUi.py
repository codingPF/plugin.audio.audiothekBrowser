# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import xbmcplugin
import xbmcgui
import resources.lib.utils as pyUtils
import resources.lib.ui.listModel as ListModel
import resources.lib.appContext as appContext


class ListUI(object):

    def __init__(self, pAddon, pTargetMode):
        self.logger = appContext.LOGGER.getInstance('ListUI')
        self.setting = appContext.SETTINGS
        self.addon = pAddon
        self.targetMode = pTargetMode

    def generate(self, pData):
        #
        xbmcplugin.addSortMethod(self.addon.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.addon.addon_handle, 'movies')
        #
        listOfElements = []
        listItemModel = ListModel.ListModel()
        for element in pData:
            listItemModel.init(element[0], element[1], element[2])
            listOfElements.append(self.generateItem(listItemModel))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.addon.addon_handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.addon.addon_handle, cacheToDisc=False)
        self.addon.setViewId(self.addon.resolveViewId('THUMBNAIL'))

    def generateItem(self, pListItemModel):
        #
        if self.addon.getKodiVersion() > 17:
            listItem = xbmcgui.ListItem(label=pListItemModel.name, offscreen=True)
        else:
            listItem = xbmcgui.ListItem(label=pListItemModel.name)
        #
        icon = pListItemModel.image.replace('{ratio}', self.setting.getIconRatio()).replace('{width}', self.setting.getIconSize())
        # self.logger.debug('icon {}', icon)
        #
        listItem.setArt({
            'thumb': icon,
            'icon': icon,
            'banner': icon,
            'fanart': icon,
            'clearart': icon,
            'clearlogo': icon
        })
        #
        targetUrl = pyUtils.build_url({
                'mode': self.targetMode,
                'id' : pListItemModel.id
        })
        #
        return (targetUrl, listItem, True)

