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


class RefreshArdAudiothek(object):
    """
    RefreshArdAudiothek

    """

    def __init__(self, pDb):
        self.logger = appContext.LOGGER.getInstance('RefreshArdAudiothek')
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

    def loadShows(self):
        #
        # dataString = pyUtils.url_to_string('https://api.ardaudiothek.de/organizations/')
        dn = WebResource.WebResource('https://api.ardaudiothek.de/organizations/')
        dataString = dn.retrieveAsString()
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
                #
                if publicationService.get('_embedded').get('mt:liveStreams').get('_embedded') != None \
                and publicationService.get('_embedded').get('mt:liveStreams').get('numberOfElements') > 0:
                    livestreamArray = []
                    testLivestreamArray = publicationService.get('_embedded').get('mt:liveStreams').get('_embedded').get('mt:items')
                    if isinstance(testLivestreamArray, list):
                        livestreamArray = testLivestreamArray
                    else:
                        livestreamArray.append(testLivestreamArray)
                    #
                    for livestreamElement in livestreamArray:
                        if livestreamElement.get('stream') != None:
                            elementChannelLivestream = livestreamElement.get('stream').get('streamUrl')
                            self.db.addLivestream(elementChannel, ('ARD', elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream, elementChannelDescription))
                            break
                else:
                    elementChannelLivestream = ''
                # self.logger.debug("CHANNEL: {} # {} # {} # {}", elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream)
                #
                # one element is not retured as array
                showArray = []
                nextElement = publicationService.get('_embedded').get('mt:programSets')
                if isinstance(nextElement, list):
                    showArray = nextElement
                else:
                    showArray.append(nextElement)
                #
                for show in showArray:
                    showId = show.get('id')
                    showName = show.get('title')
                    showImage = show.get('_links').get('mt:image').get('href')
                    categoryTitle = show.get('_embedded').get('mt:editorialCategories').get('title')
                    # self.logger.debug("BROADCAST: {} # {} # {}", showId , showName, showImage)
                    self.recordShowCount += 1
                    self.insertShowCount += self.db.addShow(showId, ('ARD', elementOrganizationId, elementOrganizationName, elementOrganizationImage, elementChannel, elementChannelName, elementChannelImage, showId, showName, showImage, categoryTitle))
                    #
                    # self.loadEpisode(showId)
                    #
                    self.kodiPG.update(int(self.recordShowCount / 10))
        #
        self.logger.info('refreshed ard shows ( {} / {} ) in {} sec(s)', self.insertShowCount, self.recordShowCount, (time.time() - self.starttime))

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
        url = 'https://api.ardaudiothek.de/programsets/{}?limit=999'.format(pBroadcast)
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
            self.insertEpisodeCount += self.db.addEpisode(episodeId, ('ARD', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, int(time.time())))
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
