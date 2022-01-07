# -*- coding: utf-8 -*-
"""
The main addon module

SPDX-License-Identifier: MIT

"""
import xbmcplugin
import time
import os
import resources.lib.appContext as appContext
import resources.lib.utils as pyUtils
import resources.lib.kodiUi as KodiUI
import resources.lib.sqliteDB as SqliteDb
from resources.lib.ardAudiothekGql import ArdAudiothekGql
from resources.lib.kodi import Kodi
import resources.lib.kodiProgressDialog as PG
#


class Main(Kodi):

    def __init__(self):
        super(Main, self).__init__()
        self.logger = appContext.LOGGER.getInstance('Main')
        self.settings = appContext.SETTINGS
        # ensure we have settings and a addon data directory
        self.setSetting('lastUsed', str(int(time.time())))
        #
        self.db = SqliteDb.SqliteDB(pyUtils.createPath((self.getAddonDataPath(), 'audiothekDB.db')))
        # print(datetime.datetime.strptime("21/11/06 16:30", "%d/%m/%y %H:%M"))
        # print(str(pyUtils.epoch_from_timestamp('2020-11-07T16:12:13.987+0100', '%Y-%m-%dT%H:%M:%S.%f%z')))
        self.refresh = ArdAudiothekGql(self.db, self.getAbortHook())
        self.refresh.run()
        #

    def run(self):
        #
        mode = self.getParameters('mode')
        parameterId = self.getParameters('id')
        self.logger.info('Run Plugin with Parameters {}', self.getParameters())
        if mode == 'organization':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genList(mmUI, self.db.getOrganizations(), 'channel')
            #
        elif mode == 'channel':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genList(mmUI, self.db.getChannel(parameterId),'broadcast')
            #
        elif mode == 'broadcast':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genList(mmUI, self.db.getBroadcast(parameterId),'episode')
            #
        elif mode == 'episode':
            self.refresh.loadEpisode(parameterId)
            mmUI = KodiUI.KodiUI(self, 'audio')
            self.genItems(mmUI, self.db.getEpisodes(parameterId))
            #            
        elif mode == 'tags':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genList(mmUI, self.db.getTags(parameterId), 'tag')
            #
        elif mode == 'tag':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genList(mmUI, self.db.getTag(parameterId), 'episode')
            #
        elif mode == 'livestream':
            mmUI = KodiUI.KodiUI(self, 'movies', [xbmcplugin.SORT_METHOD_TITLE])
            self.genLivestream(mmUI, self.db.getLivestream())
            #
        elif mode == 'search':
            pQuery = self.get_entered_text()
            if pQuery and pQuery[1]:
                cmd = 'Container.refresh({})'.format(self.generateUrl({'mode': "searchQuery",'queryString': pQuery[0]}))
                self.logger.debug('cmd {}',cmd)
                xbmcplugin.endOfDirectory(self.addon_handle, cacheToDisc=False)
                self.executebuiltin(cmd)
            #
        elif mode == 'searchQuery':
            mmUI = KodiUI.KodiUI(self, 'audio', [xbmcplugin.SORT_METHOD_TITLE])
            query = self.getParameters('queryString')
            if query:
                self.genSeachItems(mmUI, self.refresh.query(query))
            #
        elif mode == 'download':
            kodiPG = PG.KodiProgressDialog()
            kodiPG.create(30102)
            #
            url = self.getParameters('targetUrl')
            name = self.getParameters('filename')
            fullName = pyUtils.createPath((self.translatePath(self.settings.getDownloadPath()), name))
            pyUtils.url_retrieve(url, fullName, reporthook=kodiPG.update, chunk_size=65536, aborthook=self.getAbortHook())
            #
            kodiPG.close()
            #
        elif mode == 'refresh':
            self.db.reset()
            self.executebuiltin('Container.Refresh')
            #
        else:
            mmUI = KodiUI.KodiUI(self, '', [xbmcplugin.SORT_METHOD_TITLE])
            self.getMainMenuData(mmUI)
        #
        self.db.exit()

    ##########

    def getMainMenuData(self, pUI):
        pUI.addListItem(
                pTitle=self.localizeString(30001), 
                pUrl=self.generateUrl({'mode': 'organization'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-org.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30002), 
                pUrl=self.generateUrl({'mode': 'channel'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-channel.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30003), 
                pUrl=self.generateUrl({'mode': 'broadcast'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-broadcast.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30005), 
                pUrl=self.generateUrl({'mode': 'livestream'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-livestream.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30010), 
                pUrl=self.generateUrl({'mode': 'tags'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-tags.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30011), 
                pUrl=self.generateUrl({'mode': 'search'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-search.png'), 
                pPlayable='False', 
                pFolder=True)
        pUI.addListItem(
                pTitle=self.localizeString(30006), 
                pUrl=self.generateUrl({'mode': 'refresh'}), 
                pIcon=os.path.join(self.getAddonPath(), 'resources', 'icons', 'icon-refresh.png'), 
                pPlayable='False', 
                pFolder=True)
        #
        pUI.render()
                

    ############
    #
    # specific transformations
    #
    ###########
    
    # id, name, imgage
    def genList(self, pUI, pData, pTargetMode):
        for element in pData:
            icon = None
            if element[2]:
                icon = element[2].replace('{ratio}', self.settings.getIconRatio()).replace('{width}', self.settings.getIconSize())
            #
            targetUrl = pyUtils.build_url({
                'mode': pTargetMode,
                'id' : element[0]
                })
            pUI.addListItem(
                pTitle=element[1], 
                pUrl=targetUrl, 
                pIcon=icon, 
                pPlayable='False', 
                pFolder=True)
        #
        pUI.render()
        #
        self.setViewId(self.resolveViewId('THUMBNAIL'))
        #

    #episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, created
    def genItems(self, pUI, pData):
        for element in pData:
            icon = None
            if element[6]:
                icon = element[6].replace('{ratio}', self.settings.getIconRatio()).replace('{width}', self.settings.getIconSize())
            #
            cm = [(self.localizeString(30100),'RunPlugin({})'.format(self.generateUrl( { 'mode': 'download', 'filename': pyUtils.file_cleanupname(element[1]), 'targetUrl': element[5]})))]
            #
            pUI.addListItem(
                pTitle=element[1], 
                pUrl=element[5], 
                pPlot=element[4],
                pDuration=element[2],
                pAired=element[3],
                pIcon=icon,
                pContextMenu=cm
            )
        #
        pUI.render()
        #

    #livestreamId, livestreamName, livestreamImage, livestreamUrl, livestreamDescription
    def genLivestream(self, pUI, pData):
        for element in pData:
            icon = None
            if element[2]:
                icon = element[2].replace('{ratio}', self.settings.getIconRatio()).replace('{width}', self.settings.getIconSize())
            #
            pUI.addListItem(
                pTitle=element[1], 
                pUrl=element[3], 
                pIcon=icon
            )
        #
        pUI.render()
        #
        self.setViewId(self.resolveViewId('THUMBNAIL'))
        #

    # id, title, image, url, duration, publishDate, synopsis
    def genSeachItems(self, pUI, pData):
        for element in pData:
            icon = None
            if element[2]:
                icon = element[2].replace('{ratio}', self.settings.getIconRatio()).replace('{width}', self.settings.getIconSize())
            #
            if len(element) > 3:
                cm = [(self.localizeString(30100),'RunPlugin({})'.format(self.generateUrl( { 'mode': 'download', 'filename': pyUtils.file_cleanupname(element[1]), 'targetUrl': element[3]})))]
                #
                pUI.addListItem(
                    pTitle=element[1], 
                    pUrl=element[3], 
                    pPlot=element[6],
                    pDuration=element[4],
                    pAired=element[5],
                    pIcon=icon,
                    pContextMenu=cm
                )
            else:
                targetUrl = pyUtils.build_url({
                    'mode': 'episode',
                    'id' : element[0]
                })
                pUI.addListItem(
                    pTitle=element[1], 
                    pUrl=targetUrl, 
                    pIcon=icon,
                    pPlayable='False', 
                    pFolder=True
                )
        #
        pUI.render()
        #