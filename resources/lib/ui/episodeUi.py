# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import xbmcplugin
import xbmcgui
import datetime
import resources.lib.utils as pyUtils
import resources.lib.ui.episodeModel as EpisodeModel
import resources.lib.appContext as appContext


class EpisodeUI(object):

    def __init__(self, pAddon):
        self.logger = appContext.LOGGER.getInstance('EpisodeUI')
        self.setting = appContext.SETTINGS
        self.addon = pAddon
        self.tzBase = datetime.datetime.fromtimestamp(0)
        self.allSortMethods = [
            xbmcplugin.SORT_METHOD_UNSORTED,
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_DATE,
            xbmcplugin.SORT_METHOD_DATEADDED,
            xbmcplugin.SORT_METHOD_DURATION
        ]

    def generate(self, pData):
        #
        for method in self.allSortMethods:
            xbmcplugin.addSortMethod(self.addon.addon_handle, method)
        xbmcplugin.setContent(self.addon.addon_handle, 'audio')
        #
        listOfElements = []
        episodeModel = EpisodeModel.EpisodeModel()
        for element in pData:
            episodeModel.init(element[0], element[1], element[2], element[3],
                              element[4], element[5], element[6], element[7])
            #
            (targetUrl, listItem, isFolder) = self._generateListItem(episodeModel)
            #
            listItem.addContextMenuItems(self._generateContextMenu(episodeModel))
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
        # self.addon.setViewId(self.addon.resolveViewId('THUMBNAIL'))

    def _generateListItem(self, pEpisode):
        #
        info_labels = {
            'title': pEpisode.title,
            'sorttitle': pEpisode.title.lower(),
            'tvshowtitle': pEpisode.title,
            'plot': pEpisode.description
        }
        #
        if info_labels['plot'] is None:
            info_labels['plot'] = ''

        if pEpisode.duration is not None and pEpisode.duration > 0:
            info_labels['duration'] = '{:02d}:{:02d}:00'.format(*divmod(pEpisode.duration, 60))

        if pEpisode.aired is not None and pEpisode.aired != 0:
            ndate = self.tzBase + datetime.timedelta(seconds=(pEpisode.aired))
            airedstring = ndate.isoformat().replace('T', ' ')
            info_labels['date'] = airedstring[:10]
            info_labels['aired'] = airedstring[:10]
            info_labels['dateadded'] = airedstring
            info_labels['plot'] = self.addon.localizeString(30101).format(airedstring) + info_labels['plot']

        icon = pEpisode.image.replace('{ratio}', self.setting.getIconRatio()).replace('{width}', self.setting.getIconSize())

        #
        if self.addon.getKodiVersion() > 17:
            listitem = xbmcgui.ListItem(label=pEpisode.title, path=pEpisode.url, offscreen=True)
        else:
            listitem = xbmcgui.ListItem(label=pEpisode.title, path=pEpisode.url)
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
        return (pEpisode.url, listitem, False)

    def _generateContextMenu(self, pEpisode):
        contextmenu = []

        contextmenu.append((
            self.addon.localizeString(30100),
            'RunPlugin({})'.format(
                self.addon.generateUrl({
                    'mode': "download",
                    'id': pEpisode.id
                })
            )
        ))
        return contextmenu

