# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import xbmcplugin
import xbmcgui
import datetime
import resources.lib.utils as pyUtils
import resources.lib.ui.livestreamModel as LivestreamModel
import resources.lib.appContext as appContext


class LivestreamUI(object):

    def __init__(self, pAddon):
        self.logger = appContext.LOGGER.getInstance('EpisodeUI')
        self.setting = appContext.SETTINGS
        self.addon = pAddon
        self.tzBase = datetime.datetime.fromtimestamp(0)

    def generate(self, pData):
        #
        xbmcplugin.addSortMethod(self.addon.addon_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.addon.addon_handle, 'movies')
        #
        listOfElements = []
        livestreamModel = LivestreamModel.LivestreamModel()
        for element in pData:
            livestreamModel.init(element[0], element[1], element[2], element[3], element[4])
            #
            (targetUrl, listItem, isFolder) = self._generateListItem(livestreamModel)
            #
            listOfElements.append((targetUrl, listItem, isFolder))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.addon.addon_handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.addon.addon_handle, cacheToDisc=False)
        self.addon.setViewId(self.addon.resolveViewId('THUMBNAIL'))

    def _generateListItem(self, pLivestreamModel):
        #
        info_labels = {
            'title': pLivestreamModel.title,
            'sorttitle': pLivestreamModel.title.lower(),
            'tvshowtitle': pLivestreamModel.title,
            'plot': pLivestreamModel.description
        }
        #
        icon = pLivestreamModel.image.replace('{ratio}', self.setting.getIconRatio()).replace('{width}', self.setting.getIconSize())
        #
        if self.addon.getKodiVersion() > 17:
            listitem = xbmcgui.ListItem(label=pLivestreamModel.title, path=pLivestreamModel.url, offscreen=True)
        else:
            listitem = xbmcgui.ListItem(label=pLivestreamModel.title, path=pLivestreamModel.url)
        #
        listitem.setInfo(type='video', infoLabels=info_labels)
        listitem.setProperty('IsPlayable', 'true')
        listitem.setArt({
            'thumb': icon,
                'icon': icon,
                'banner': icon,
                'fanart': icon,
                'clearart': icon,
                'clearlogo': icon
        })
        #
        return (pLivestreamModel.url, listitem, False)

