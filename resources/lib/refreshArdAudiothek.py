# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
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


class RefreshArdAudiothek(object):
    """
    RefreshArdAudiothek

    """

    def __init__(self, pDb):
        self.logger = appContext.LOGGER.getInstance('RefreshArdAudiothek')
        self.settings = appContext.SETTINGS
        self.db = pDb
        self.insertCategoryCount = 0
        self.recordCategoryCount = 0
        self.insertEpisodeCount = 0
        self.recordEpisodeCount = 0
        self.kodiPG = None
        self.starttime = time.time()

    def run(self):
        #
        if not(self.db.isInitialized()):
            self.settings.setLastUpdateIndex('0')
            self.db.create()
        #
        self.loadcategory()
        #

    def loadcategory(self):
        #
        age = int((time.time() - self.settings.getLastUpdateIndex()) / 60)
        if age < self.settings.getUpdateInterval():
            self.logger.debug('Index is up-to-date age: {} / {}', age, self.settings.getUpdateInterval())
            return
        else:
            self.logger.debug('Update index due to age: {} / {} last {} cTime {}', age, self.settings.getUpdateInterval(), self.settings.getLastUpdateIndex(), int(time.time()))
        #
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30006)
        # dataString = pyUtils.url_to_string('https://api.ardaudiothek.de/organizations/')
        dn = WebResource.WebResource('https://api.ardaudiothek.de/organizations/')
        dataString = dn.retrieveAsString()
        #
        self.db.deleteCategory();
        self.db.deleteLivestream();
        #
        data = json.loads(dataString)
        #
        data = data.get('_embedded').get('mt:organizations')
        for organization in data:
            elementOrganizationId = organization.get('id')
            elementOrganizationName = organization.get('name')
            elementOrganizationImage = organization.get('_links').get('mt:image').get('href')
            # self.logger.debug("ORGA: {} # {} # {}", elementOrganizationId, elementOrganizationName, elementOrganizationImage)
            #
            # one element is not retured as array
            publicationArray = []
            nextElement = organization.get('_embedded').get('mt:publicationServices')
            if isinstance(nextElement, list):
                publicationArray = nextElement
            else:
                publicationArray.append(nextElement)
            #
            for publicationService in publicationArray:
                elementChannel = publicationService.get('id')
                elementChannelName = publicationService.get('title')
                elementChannelDescription = publicationService.get('synopsis')
                elementChannelImage = publicationService.get('_links').get('mt:image').get('href')
                if publicationService.get('_embedded').get('mt:liveStreams').get('_embedded') != None:
                    elementChannelLivestream = publicationService.get('_embedded').get('mt:liveStreams').get('_embedded').get('mt:items').get('stream').get('streamUrl')
                    self.db.addLivestream(elementChannel, (elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream, elementChannelDescription))
                else:
                    elementChannelLivestream = ''
                # self.logger.debug("CHANNEL: {} # {} # {} # {}", elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream)
                #
                # one element is not retured as array
                categoryArray = []
                nextElement = publicationService.get('_embedded').get('mt:programSets')
                if isinstance(nextElement, list):
                    categoryArray = nextElement
                else:
                    categoryArray.append(nextElement)
                #
                for category in categoryArray:
                    categoryId = category.get('id')
                    categoryName = category.get('title')
                    categoryImage = category.get('_links').get('mt:image').get('href')
                    # self.logger.debug("BROADCAST: {} # {} # {}", categoryId , categoryName, categoryImage)
                    self.recordCategoryCount += 1
                    self.insertCategoryCount += self.db.addCategory(categoryId, (elementOrganizationId, elementOrganizationName, elementOrganizationImage, elementChannel, elementChannelName, elementChannelImage, categoryId, categoryName, categoryImage))
                    #
                    # self.loadEpisode(categoryId)
                    #
                    self.kodiPG.update(int(self.recordCategoryCount / 10))
        #
        self.settings.setLastUpdateIndex(str(int(time.time())))
        self.kodiPG.close()
        self.logger.info('last update {} vs {}', str(int(time.time())), self.settings.getLastUpdateIndex())
        #
        self.logger.info('refreshed categories ( {} / {} ) in {} sec(s)', self.insertCategoryCount, self.recordCategoryCount, (time.time() - self.starttime))

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
        url = 'https://api.ardaudiothek.de/programsets/{}'.format(pBroadcast)
        self.logger.debug('Download {}', url)
        # dataString = pyUtils.url_to_string(url)
        dn = WebResource.WebResource(url)
        dataString = dn.retrieveAsString()
        #
        data = json.loads(dataString)
        #
        episodeArray = []
        data = data.get('_embedded').get('mt:items')
        if data == None:
            return
        elif isinstance(data, list):
            episodeArray = data
        else:
            episodeArray.append(data)
        #
        for episode in episodeArray:
            episodeId = episode.get('id')
            episodeTitle = episode.get('title')
            episodeDuration = episode.get('duration')
            episodeAired = self._parseTimestamp(episode.get('publicationStartDateAndTime'))
            episodeDescription = episode.get('synopsis')
            episodeUrl = episode.get('_links').get('mt:bestQualityPlaybackUrl').get('href')
            # episodeUrl = episode.get('_links').get('mt:downloadUrl').get('href')
            episodeImage = episode.get('_links').get('mt:image').get('href')
            self.recordEpisodeCount += 1
            self.insertEpisodeCount += self.db.addEpisode(episodeId, (pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, int(time.time())))
            # self.logger.debug('EPOSIODE {} # {} # {} # {} # {}', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage)
        #
        self.db.setLastLoadEpisode(pBroadcast)
        self.logger.info('loadEpisode ( {} / {} ) in {} sec(s)', self.insertEpisodeCount, self.recordEpisodeCount, (time.time() - self.starttime))

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
