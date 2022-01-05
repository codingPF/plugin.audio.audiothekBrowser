# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import time
import xbmcplugin
import xbmcgui
import datetime
import resources.lib.appContext as appContext

class KodiUI(object):

    ###########
    #
    ###########
    def __init__(self, pAddon, pContentType = 'video', pSortMethods = None, pCacheToDisc = False ):
        self.logger = appContext.LOGGER.getInstance('KodiUI')
        self.setting = appContext.SETTINGS
        self.addon = pAddon
        #
        self.allSortMethods = [
            xbmcplugin.SORT_METHOD_UNSORTED,
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_DATE,
            xbmcplugin.SORT_METHOD_DATEADDED,
            xbmcplugin.SORT_METHOD_DURATION
        ]
        if pSortMethods is not None:
            self.allSortMethods = pSortMethods
        #
        self.contentType = pContentType
        self.cacheToDisc = pCacheToDisc
        self.listItems = []
        self.startTime = 0
        self.tzBase = datetime.datetime.fromtimestamp(0)


    def addListItem(self, pTitle, pUrl, pSortTitle = None, pPlot = None, pDuration = None, pAired = None, pIcon = None, pContextMenu = None, pPlayable = 'True', pFolder = False):
        #
        if self.startTime == 0:
            self.startTime = time.time()
        #
        if self.addon.getKodiVersion() > 17:
            listItem = xbmcgui.ListItem(label=pTitle, path=pUrl, offscreen=True)
        else:
            listItem = xbmcgui.ListItem(label=pTitle, path=pUrl)
        #
        if pPlayable == 'True':
            info_labels = {
                'title': pTitle,
                'sorttitle': pSortTitle if pSortTitle else pTitle.lower(),
                'tvshowtitle': pTitle,
                'plot': pPlot if pPlot else ''
            }
            #
            if pDuration:
                info_labels['duration'] = '{:02d}:{:02d}:00'.format(*divmod(pDuration, 60))
            #
            if pAired:
                ndate = self.tzBase + datetime.timedelta(seconds=(pAired))
                airedstring = ndate.isoformat().replace('T', ' ')
                info_labels['date'] = airedstring[:10]
                info_labels['aired'] = airedstring[:10]
                info_labels['dateadded'] = airedstring
                #
                info_labels['plot'] = self.addon.localizeString(30101).format(airedstring) + info_labels['plot']
                #
            # tpye is video to have plot and aired date etc.
            listItem.setInfo(type='video', infoLabels=info_labels)
            #
        #
        listItem.setProperty('IsPlayable', pPlayable)
        #
        if pIcon:
            listItem.setArt({
                'thumb': pIcon, #video 16:9 960w x 540h / Music 1:1 500w x 500h 
                'icon': pIcon, #16:9 640w x 360h 
                'banner': pIcon, #200:37 1000w x 185h 
                'fanart': pIcon, #16:9 1920w x 1080h
                'clearart': pIcon, # 16:9  1000w x 562h
                'clearlogo': pIcon # 80:31 800w x 310h 
            })
        #[('title1','action1'),('title2','action2'),...]
        if pContextMenu:
            listItem.addContextMenuItems(pContextMenu)
        #
        self.listItems.append((pUrl, listItem, pFolder))
        #

    def render(self):
        #
        for method in self.allSortMethods:
            xbmcplugin.addSortMethod(self.addon.addon_handle, method)
        #
        xbmcplugin.setContent(self.addon.addon_handle, self.contentType)
        #
        xbmcplugin.addDirectoryItems(
            handle=self.addon.addon_handle,
            items=self.listItems,
            totalItems=len(self.listItems)
        )
        #
        xbmcplugin.endOfDirectory(self.addon.addon_handle, cacheToDisc=self.cacheToDisc)
        #
        self.logger.debug('generated {} item(s) in {} sec', len(self.listItems), round(time.time() - self.startTime, 4))


