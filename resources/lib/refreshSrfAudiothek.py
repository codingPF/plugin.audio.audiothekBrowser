# -*- coding: utf-8 -*-
"""
The local SQlite database module
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import json
import datetime
import time
import resources.lib.appContext as appContext
import resources.lib.utils as pyUtils
import resources.lib.kodiProgressDialog as PG
import resources.lib.webResource as WebResource



class RefreshSrfAudiothek(object):
    """
    RefreshSRFAudiothek

    """

    def __init__(self, pDb):
        self.logger = appContext.LOGGER.getInstance('RefreshSRFAudiothek')
        self.settings = appContext.SETTINGS
        self.db = pDb
        self.insertShowCount = 0
        self.recordShowCount = 0
        self.insertEpisodeCount = 0
        self.recordEpisodeCount = 0
        self.kodiPG = None
        self.starttime = time.time()

    def run(self):
        #
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30006)
        #
        self.loadShows()
        #
        self.kodiPG.close()

    def _delete_me_loadLivestream(self):
        dn = WebResource.WebResource('https://il.srgssr.ch/integrationlayer/2.0/srf/mediaList/audio/livestreams.json')
        dataString = dn.retrieveAsString()
        data = json.loads(dataString)
        for channel in data.get('mediaList'):
            cId = channel.get('id')
            cVendor = channel.get('vendor')
            cUrn = channel.get('urn')
            cTitle = channel.get('title')
            cDescription = channel.get('description')
            cImage = channel.get('imageUrl')                      
            self.db.addLivestream(cUrn, ('SRF', cUrn, cTitle, cImage, self.resolveMediaFile(cUrn), cDescription))
            self.kodiPG.update(int(len(channel) / 10))
            
    
    def resolveMediaFile(self, cUrn):
        cUrl = "https://il.srgssr.ch/integrationlayer/2.0/mediaComposition/byUrn/{}.json?onlyChapters=true&vector=portalplay".format(cUrn)
        #self.logger.debug('livestream query url {}', cUrl);
        dn = WebResource.WebResource(cUrl)
        dataString = dn.retrieveAsString()
        data = json.loads(dataString)
        pickFirst = ''
        pickM3U8 = ''
        for c in data.get('chapterList'):
            for resourceList in c.get('resourceList'):
                if pickFirst == '':
                    pickFirst = resourceList.get('url')
                if resourceList.get('url').endswith('m3u8') and pickM3U8 == '':
                    pickM3U8 = resourceList.get('url')
        if pickM3U8 == '':
            pickM3U8 = pickFirst
        #self.logger.debug('livestream target url {}', pickM3U8);
        return pickM3U8
        
    
    def loadShows(self):
        #
        #
        dn = WebResource.WebResource('https://il.srgssr.ch/integrationlayer/2.0/srf/mediaList/audio/livestreams.json')
        dataString = dn.retrieveAsString()
        data = json.loads(dataString)
        #
        source = 'SRF'
        orgId = 'SRF'
        orgName = 'SRF'
        orgImage = 'https://www.srf.ch/extension/srf_shared/design/standard/images/favicons/apple-touch-icon-180x180.png'
        #
        for channel in data.get('mediaList'):
            channelId = channel.get('id')
            channelTitle = channel.get('title')
            channelUrn = channel.get('urn')  
            channelDescription = channel.get('description')
            channelImage = channel.get('imageUrl')                      
            self.db.addLivestream(channelUrn, ('SRF', channelUrn, channelTitle, channelImage, self.resolveMediaFile(channelUrn), channelDescription))
            #
            wrShows = WebResource.WebResource('https://il.srgssr.ch/integrationlayer/2.0/srf/showList/radio/alphabeticalByChannel/{}.json?pageSize=99'.format(channelId))
            showString = wrShows.retrieveAsString()
            showData = json.loads(showString)
            for show in showData.get('showList'):
                #
                showId = show.get('id')
                showName = show.get('title')
                showImage = show.get('imageUrl')
                showUrn = show.get('urn')
                #
                categoryTitle = ''
                self.recordShowCount += 1
                self.insertShowCount += self.db.addShow(showUrn, (source, orgId, orgName, orgImage, channelId, channelTitle, channelImage, showUrn, showName, showImage, categoryTitle))
                #
                # self.loadEpisode(showId)
                #
                self.kodiPG.update(int(self.recordShowCount / 3))
        #
        self.logger.info('refreshed shows ( {} / {} ) in {} sec(s)', self.insertShowCount, self.recordShowCount, (time.time() - self.starttime))

    def loadEpisode(self, pBroadcast):
        #
        lastUpdate = self.db.getastLoadEpisode(pBroadcast)
        age = int((time.time() - lastUpdate) / 60)
        if (age < self.settings.getUpdateInterval()):
            self.logger.debug('Episode is up-to-date age: {} / {}', age, self.settings.getUpdateInterval())
            return
        else:
            self.logger.debug('Update Episodes age: {} / {} last {} cTime {}', age, self.settings.getUpdateInterval(), lastUpdate, int(time.time()))
        #
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.startBussyDialog()
        #
        url = 'https://il.srgssr.ch/integrationlayer/2.0/episodeComposition/latestByShow/byUrn/{}.json'.format(pBroadcast)
        next = url
        cnt = 0
        self.logger.debug('Download {}', url)
        while next is not None:
            next = self._processEpisodePage(pBroadcast, next)
            cnt += 1
            self.logger.info('Loop ({}) for Episodes per show ({})',cnt,pBroadcast )
            if cnt > self.settings.getMaxFilesPerShow():
                next = None
                self.logger.info('Max ({}) Episodes per show ({}) reached and aborting download!',self.settings.getMaxFilesPerShow(),pBroadcast )
        #
        self.db.setLastLoadEpisode(pBroadcast)
        self.logger.info('loadEpisode ( {} / {} ) in {} sec(s)', self.insertEpisodeCount, self.recordEpisodeCount, (time.time() - self.starttime))

    def _processEpisodePage(self, pBroadcast, nextUrl):
        #
        dn = WebResource.WebResource(nextUrl)
        dataString = dn.retrieveAsString()
        #
        data = json.loads(dataString)
        #
        episodeArray = []
        next = data.get('next')
        data = data.get('episodeList')
        if data == None:
            return
        elif isinstance(data, list):
            episodeArray = data
        else:
            episodeArray.append(data)
        #
        for episode in episodeArray:
            episodeId = episode.get('fullLengthUrn')
            episodeTitle = episode.get('title')
            episodeImage = episode.get('imageUrl')
            episodeAired = self._parseTimestamp(episode.get('publishedDate'))
            episodeDuration = episode.get('mediaList')[0].get('duration')/1000
            episodeDescription = episode.get('mediaList')[0].get('description')
            episodeUrl = episode.get('mediaList')[0].get('podcastHdUrl')
            if episodeUrl is None:
                episodeUrl = self.resolveMediaFile(episode.get('fullLengthUrn'))
                
            self.recordEpisodeCount += 1
            self.insertEpisodeCount += self.db.addEpisode(episodeId, ('SRF', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, int(time.time())))
            # self.logger.debug('EPOSIODE {} # {} # {} # {} # {}', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage)
        return next

    def _parseTimestamp(self, pTimestamp):
        y = pTimestamp[0:4]
        m = pTimestamp[5:7]
        d = pTimestamp[8:10]
        hh = pTimestamp[11:13]
        mm = pTimestamp[14:16]
        ss = pTimestamp[17:19]
        ff = pTimestamp[20:23]
        tz = pTimestamp[24:29]
        tzhh = tz[0:2]
        new_time = datetime.datetime(year=int(y), month=int(m), day=int(d),
            hour=int(hh), minute=int(mm), second=int(ss))
        ref = datetime.timedelta(hours=int(tzhh))
        dt = (new_time + ref)
        return int((dt - datetime.datetime(year=1970, month=1, day=1)).total_seconds())
