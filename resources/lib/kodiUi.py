# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import time
import xbmcplugin
import xbmcgui
import xbmc
import datetime
import resources.lib.appContext as appContext

class KodiUI(object):

    ###########
    #
    ###########
    def __init__(self, pAddon, pContentType = '', pSortMethods = None, pCacheToDisc = False, pViewId = None ):
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
        self.viewId = pViewId
        self.listItems = []
        self.startTime = 0
        self.tzBase = datetime.datetime.fromtimestamp(0)
        # just for documentation
        self.docuContentTypes = ['','video','movies']


    def addDirectoryItem(self, pTitle, pUrl, pSortTitle = None, pIcon = None, pContextMenu = None):
        self.addListItem(
            pTitle=pTitle, 
            pUrl=pUrl, 
            pSortTitle=None, 
            pPlot=None, 
            pDuration= None, 
            pAired= None, 
            pIcon=pIcon, 
            pContextMenu=pContextMenu,
            pPlayable='False',
            pFolder=True)

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
            tag = listItem.getVideoInfoTag()
            tag.setTitle(pTitle)
            tag.setOriginalTitle(pTitle)
            tag.setSortTitle(pSortTitle if pSortTitle else pTitle.lower())
            tag.setTvShowTitle(pTitle)
            tag.setPlot(pPlot if pPlot else '')
            #
            if pDuration:
                tag.setDuration(pDuration)
            #
            if pAired:
                if type(pAired) in (type(''), type(u'')):
                    ndate = pAired
                else:
                    ndate = (self.tzBase + datetime.timedelta(seconds=(pAired))).isoformat()
                airedstring = ndate.replace('T', ' ')
                tag.setDateAdded(airedstring) # (YYYY-MM-DD HH:MM:SS)
                tag.setFirstAired(airedstring[:10])
                tag.setLastPlayed(airedstring) #(YYYY-MM-DD HH:MM:SS)
                tag.setPremiered(airedstring[:10])
                tag.setYear(int(airedstring[:4]))
                listItem.setDateTime(ndate) #YYYY-MM-DDThh:mm[TZD]
                tag.setPlot(self.addon.localizeString(30101).format(airedstring) + (pPlot if pPlot else ''))
                #
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
        if self.viewId:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(self.viewId))
        #
        self.logger.debug('generated {} item(s) in {} sec', len(self.listItems), round(time.time() - self.startTime, 4))


