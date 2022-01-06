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


class ArdAudiothekGql(object):
    """
    RefreshArdAudiothek
    """

    def __init__(self, pDb, pAbortHook):
        self.logger = appContext.LOGGER.getInstance('RefreshArdAudiothekGQL')
        self.settings = appContext.SETTINGS
        self.db = pDb
        self.abortHook = pAbortHook        
        self.kodiPG = None
        self.starttime = time.time()
        #
        self.apiUrl = 'https://api.ardaudiothek.de/graphql';
        #
        self.categoryQuery = """
{
 organizations {
  nodes {
   rowId
   title
   image {
    url
   }
   publicationServicesByOrganizationName {
    nodes {
     rowId
     title
     organizationName
     synopsis
     genre
     numberOfElements
     homepageUrl
     image {
      url
     }
     permanentLivestreams {
      nodes {
       image {
        url
       }
       audios {
        url
       }
      }
     }
     programSets {
      nodes {
       numberOfElements
       id
       editorialCategory {
        image {
         url
        }
        title
       }
       synopsis
       title
       image {
        url
       }
      }
     }
    }
   }
  }
 }
}
"""
        self.episodeQuery = """
query($id:Int!, $offset:Int!, $limit:Int!) {
 programSet(id: $id) {
  id
  title
  numberOfElements
  items(offset: $offset, first: $limit, filter: {isPublished: {equalTo: true}}) {
   nodes {
    id
    title
    synopsis
    duration
    publishDate
    image {
     url
    }
    audios {
     url
    }
    programSet {
     id
     title
    }
   }
  }
 }
}
"""
        self.searchQuery = """
query ($query:String!, $offset:Int!, $limit:Int!) {
 search(query: $query, offset: $offset, limit: $limit) {
  programSets {
   nodes {
     id
     title
     image {
      url
     }
   }
  }
  items {
   nodes {
    id
    title
    synopsis
    duration
    publishDate
    image {
     url
    }
    audios {
     url
    }
    programSet {
     id
     title
    }
   }
  }
 }
}
        """
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
        recordCategoryCount = 0
        insertCategoryCount = 0
        #
        age = int((time.time() - self.settings.getLastUpdateIndex()) / 60)
        if age < self.settings.getUpdateInterval():
            self.logger.debug('Index is up-to-date age: {} / {}', age, self.settings.getUpdateInterval())
            return
        else:
            self.logger.debug('Update index due to age: {} / {} last {} cTime {}', age, self.settings.getUpdateInterval(), self.settings.getLastUpdateIndex(), int(time.time()))
        #
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30100)
        # dataString = pyUtils.url_to_string('https://api.ardaudiothek.de/organizations/')
        try:
            url = pyUtils.build_external_url(self.apiUrl, {'query':self.categoryQuery})
            self.logger.debug('url {}',url)
            dn = WebResource.WebResource(url, pProgressListener=self.kodiPG.updateProgress, pAbortHook=self.abortHook)
            dataString = dn.retrieveAsString()
        except Exception as err:
            self.logger.error('Failure downloading {}', err)
            self.kodiPG.close()
            raise
        #
        self.kodiPG.create(30006)
        self.db.deleteCategory();
        self.db.deleteLivestream();
        #
        data = json.loads(dataString)
        #
        data = data.get('data').get('organizations').get('nodes')
        for organization in data:
            elementOrganizationId = organization.get('rowId')
            elementOrganizationName = organization.get('title')
            elementOrganizationImage = None
            # self.logger.debug("ORGA: {} # {} # {}", elementOrganizationId, elementOrganizationName, elementOrganizationImage)
            #
            # one element is not retured as array
            publicationArray = []
            nextElement = organization.get('publicationServicesByOrganizationName').get('nodes')
            if isinstance(nextElement, list):
                publicationArray = nextElement
            else:
                publicationArray.append(nextElement)
            #
            # i want images very hard
            for publicationService in publicationArray:
                if publicationService.get('organizationName').upper() == publicationService.get('title').upper():
                    elementOrganizationImage = self._templateImages(publicationService.get('image').get('url'))
            if not elementOrganizationImage:
                elementOrganizationImage = self._templateImages(publicationArray[0].get('image').get('url'))
            #
            for publicationService in publicationArray:
                elementChannel = publicationService.get('rowId')
                elementChannelName = publicationService.get('title')
                elementChannelOrganization = publicationService.get('organizationName')
                elementChannelDescription = publicationService.get('synopsis')
                elementChannelImage = self._templateImages(publicationService.get('image').get('url'))
                if elementChannelOrganization == elementChannelName:
                    elementOrganizationImage = elementChannelImage
                #
                if publicationService.get('permanentLivestreams').get('nodes') != None \
                and len(publicationService.get('permanentLivestreams').get('nodes')) > 0:
                    livestreamArray = []
                    testLivestreamArray = publicationService.get('permanentLivestreams').get('nodes')
                    if isinstance(testLivestreamArray, list):
                        livestreamArray = testLivestreamArray
                    else:
                        livestreamArray.append(testLivestreamArray)
                    #
                    for livestreamElement in livestreamArray:
                        if livestreamElement.get('audios') != None:
                            elementChannelLivestream = livestreamElement.get('audios')[0].get('url')
                            self.db.addLivestream(elementChannel, (elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream, elementChannelDescription))
                            break
                else:
                    elementChannelLivestream = ''
                # self.logger.debug("CHANNEL: {} # {} # {} # {}", elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream)
                #
                # one element is not retured as array
                categoryArray = []
                nextElement = publicationService.get('programSets').get('nodes')
                if isinstance(nextElement, list):
                    categoryArray = nextElement
                else:
                    categoryArray.append(nextElement)
                #
                for category in categoryArray:
                    numberOfElement = category.get('numberOfElements')
                    if numberOfElement and int(numberOfElement) > 0:
                        categoryId = category.get('id')
                        categoryName = category.get('title')
                        categoryImage = self._templateImages(category.get('image').get('url'))
                        if category.get('editorialCategory'):
                            tags = category.get('editorialCategory').get('title')
                            tagImage = category.get('editorialCategory').get('image').get('url')
                        else:
                            tags = None
                            tagImage = None
                            self.logger.debug('this category has no tag {} {}', categoryId, categoryName);
                        # self.logger.debug("BROADCAST: {} # {} # {}", categoryId , categoryName, categoryImage)
                        recordCategoryCount += 1
                        insertCategoryCount += self.db.addCategory(categoryId, (elementOrganizationId, elementOrganizationName, elementOrganizationImage, elementChannel, elementChannelName, elementChannelImage, categoryId, categoryName, categoryImage, tags, tagImage))
                    #
                    # self.loadEpisode(categoryId)
                    #
                    self.kodiPG.updateProgress(recordCategoryCount, 1000)
        #
        self.settings.setLastUpdateIndex(str(int(time.time())))
        self.kodiPG.close()
        self.logger.info('last update {} vs {}', str(int(time.time())), self.settings.getLastUpdateIndex())
        #
        self.logger.info('refreshed categories ( {} / {} ) in {} sec(s)', insertCategoryCount, recordCategoryCount, (time.time() - self.starttime))

    def loadEpisode(self, pBroadcast):
        #
        insertEpisodeCount = 0
        recordEpisodeCount = 0
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
        self.kodiPG.create(30100)
        #
        params = {'id': int(pBroadcast), 'limit': 999, 'offset': 0}
        self.logger.debug('params: {}',json.dumps(params))
        url = pyUtils.build_external_url(self.apiUrl, {'query':self.episodeQuery, 'variables':json.dumps(params)})
        self.logger.debug('Download {}', url)
        # dataString = pyUtils.url_to_string(url)
        try:
            dn = WebResource.WebResource(url, pProgressListener=self.kodiPG.updateProgress, pAbortHook=self.abortHook)
            dataString = dn.retrieveAsString()
        except Exception as err:
            self.logger.error('Failure downloading {}', err)
            self.kodiPG.close()
            raise        
        self.kodiPG.create(30006)
        #
        data = json.loads(dataString)
        #
        episodeArray = []
        data = data.get('data').get('programSet').get('items').get('nodes')
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
            episodeAired = self._parseTimestamp(episode.get('publishDate'))
            episodeDescription = episode.get('synopsis')
            episodeUrl = episode.get('audios')[0].get('url')
            episodeImage = self._templateImages(episode.get('image').get('url'))
            recordEpisodeCount += 1
            insertEpisodeCount += self.db.addEpisode(episodeId, (pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, int(time.time())))
            #
            self.kodiPG.updateProgress( recordEpisodeCount , len(episodeArray))
            # self.logger.debug('EPOSIODE {} # {} # {} # {} # {}', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage)
        #
        self.db.setLastLoadEpisode(pBroadcast)
        self.logger.info('loadEpisode ( {} / {} ) in {} sec(s)', insertEpisodeCount, recordEpisodeCount, (time.time() - self.starttime))

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

    def _templateImages(self, pImageUrl):
        return pImageUrl.replace('/16x9/{width}','/{ratio}/{width}')
    
    def query(self, pSearchTerms, pOffset=0, pLimit=999):
        #
        rs = []
        #
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30006)
        params = {'query': pSearchTerms, 'limit': pLimit, 'offset': pOffset}
        self.logger.debug('params: {}',json.dumps(params))
        url = pyUtils.build_external_url(self.apiUrl, {'query':self.searchQuery, 'variables':json.dumps(params)})
        self.logger.debug('Download {}', url)
        try:
            dn = WebResource.WebResource(url, pProgressListener=self.kodiPG.updateProgress, pAbortHook=self.abortHook)
            dataString = dn.retrieveAsString()
        except Exception as err:
            self.logger.error('Failure downloading {}', err)
            self.kodiPG.close()
            raise        
        #
        data = json.loads(dataString)
        self.logger.debug('received {}',dataString)
        #
        broadcasts = []
        broadcasts = data.get('data').get('search').get('programSets')
        #
        if broadcasts:
            for broadcast in broadcasts.get('nodes'):
                rs.append([broadcast.get('id'), broadcast.get('title'), self._templateImages(broadcast.get('image').get('url'))])
        #
        episodes = []
        episodes = data.get('data').get('search').get('items')
        if episodes:
            for episode in episodes.get('nodes'):
                rs.append([episode.get('id'), episode.get('title'), self._templateImages(episode.get('image').get('url')), episode.get('audios')[0].get('url'),episode.get('duration'),self._parseTimestamp(episode.get('publishDate')),episode.get('synopsis')])
        #
        return rs
