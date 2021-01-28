# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import xbmcplugin
import xbmcgui
import os


class MainMenuUI(object):

    def __init__(self, pAddon):
        self.addon = pAddon

    def generate(self):
        #
        xbmcplugin.addSortMethod(self.addon.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.addon.addon_handle, '')
        #
        listOfElements = []
        listOfElements.append(self.generateItem(self.addon.localizeString(30001), 'organization', 'icon-org.png'))
        listOfElements.append(self.generateItem(self.addon.localizeString(30002), 'channel', 'icon-channel.png'))
        listOfElements.append(self.generateItem(self.addon.localizeString(30003), 'broadcast', 'icon-broadcast.png'))
        listOfElements.append(self.generateItem(self.addon.localizeString(30005), 'livestream', 'icon-livestream.png'))
        listOfElements.append(self.generateItem(self.addon.localizeString(30006), 'refresh', 'icon-refresh.png'))
        xbmcplugin.addDirectoryItems(
            handle=self.addon.addon_handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.addon.addon_handle, cacheToDisc=False)
        # self.plugin.setViewId(self.plugin.resolveViewId('THUMBNAIL'))

    def generateItem(self, pName, pMode, pIcon):
        #
        if self.addon.getKodiVersion() > 17:
            listItem = xbmcgui.ListItem(label=pName, offscreen=True)
        else:
            listItem = xbmcgui.ListItem(label=pName)
        #
        icon = os.path.join(
                self.addon.getAddonPath(),
                'resources',
                'icons',
                pIcon
            )
        listItem.setArt({
            'thumb': icon,
            'icon': icon,
            'banner': icon,
            'fanart': icon,
            'clearart': icon,
            'clearlogo': icon
        })
        targetUrl = self.addon.generateUrl({
                'mode': pMode
        })
        #
        # targetUrl = 'plugin://plugin.audio.ardaudiothek/?abc=123'

        return (targetUrl, listItem, True)

