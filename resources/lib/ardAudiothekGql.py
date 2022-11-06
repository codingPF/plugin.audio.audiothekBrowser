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
     programSets( filter: { numberOfElements: { greaterThan: 0 } } ) {
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
        #self.logger.debug('dataString {}',dataString)
        data = json.loads(dataString)
        #
        data = self.makeArray(pyUtils.extractJsonValue(data, 'data', 'organizations', 'nodes'))
        for organization in data:
            elementOrganizationId = pyUtils.extractJsonValue(organization, 'rowId')
            elementOrganizationName = pyUtils.extractJsonValue(organization, 'title')
            elementOrganizationImage = None
            #
            publicationArray = self.makeArray(pyUtils.extractJsonValue(organization, 'publicationServicesByOrganizationName', 'nodes'))
            #
            # i want images very hard
            for publicationService in publicationArray:
                if pyUtils.extractJsonValue(publicationService, 'organizationName') and pyUtils.extractJsonValue(publicationService,'title') and \
                pyUtils.extractJsonValue(publicationService, 'organizationName').upper() == pyUtils.extractJsonValue(publicationService,'title').upper():
                    elementOrganizationImage = self._templateImages(pyUtils.extractJsonValue(publicationService,'image','url'))
            if not elementOrganizationImage:
                elementOrganizationImage = self._templateImages(pyUtils.extractJsonValue(publicationArray, 0,'image','url'))
            if not elementOrganizationImage:
                elementOrganizationImage = self._templateImages(pyUtils.extractJsonValue(organization,'image','url'))
            #
            #  lets do the real work
            for publicationService in publicationArray:
                elementChannel = pyUtils.extractJsonValue(publicationService, 'rowId')
                elementChannelName = pyUtils.extractJsonValue(publicationService, 'title')
                elementChannelOrganization = pyUtils.extractJsonValue(publicationService, 'organizationName')
                elementChannelDescription = pyUtils.extractJsonValue(publicationService, 'synopsis')
                elementChannelImage = self._templateImages(pyUtils.extractJsonValue(publicationService, 'image', 'url'))
                if elementChannelOrganization == elementChannelName:
                    elementOrganizationImage = elementChannelImage
                #
                testLivestreamArray = self.makeArray(pyUtils.extractJsonValue(publicationService, 'permanentLivestreams', 'nodes'))
                if len(testLivestreamArray) > 0:
                    for livestreamElement in testLivestreamArray:
                        if pyUtils.extractJsonValue(livestreamElement,'audios') != None:
                            #elementChannelLivestream = livestreamElement.get('audios')[0].get('url')
                            elementChannelLivestream = pyUtils.extractJsonValue(livestreamElement,'audios',0,'url')
                            self.db.addLivestream(elementChannel, (elementChannel, elementChannelName, elementChannelImage, elementChannelLivestream, elementChannelDescription))
                            break
                else:
                    elementChannelLivestream = ''
                #
                categoryArray = self.makeArray(pyUtils.extractJsonValue(publicationService, 'programSets', 'nodes'))
                #
                for category in categoryArray:
                    numberOfElement = category.get('numberOfElements')
                    if numberOfElement and int(numberOfElement) > 0:
                        categoryId = pyUtils.extractJsonValue(category, 'id')
                        categoryName = pyUtils.extractJsonValue(category, 'title')
                        categoryImage = self._templateImages(pyUtils.extractJsonValue(category, 'image', 'url'))
                        if pyUtils.extractJsonValue(category, 'editorialCategory'):
                            tags = pyUtils.extractJsonValue(category, 'editorialCategory', 'title')
                            tagImage = pyUtils.extractJsonValue(category, 'editorialCategory', 'image', 'url')
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
        episodeArray = self.makeArray(pyUtils.extractJsonValue(data, 'data', 'programSet', 'items', 'nodes'))
        #
        for episode in episodeArray:
            episodeId = pyUtils.extractJsonValue(episode, 'id')
            episodeTitle =  pyUtils.extractJsonValue(episode, 'title')
            episodeDuration =  pyUtils.extractJsonValue(episode, 'duration')
            episodeAired = self._parseTimestamp( pyUtils.extractJsonValue(episode, 'publishDate'))
            episodeDescription =  pyUtils.extractJsonValue(episode, 'synopsis')
            episodeUrl =  pyUtils.extractJsonValue(episode, 'audios', 0, 'url')
            episodeImage = self._templateImages(pyUtils.extractJsonValue(episode,'image','url'))
            recordEpisodeCount += 1
            insertEpisodeCount += self.db.addEpisode(episodeId, (pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, int(time.time())))
            #
            self.kodiPG.updateProgress( recordEpisodeCount , len(episodeArray))
            # self.logger.debug('EPOSIODE {} # {} # {} # {} # {}', pBroadcast, episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage)
        #
        self.db.setLastLoadEpisode(pBroadcast)
        self.logger.info('loadEpisode ( {} / {} ) in {} sec(s)', insertEpisodeCount, recordEpisodeCount, (time.time() - self.starttime))

    def _parseTimestamp(self, pTimestamp):
        if not pTimestamp:
            return None
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
        if not pImageUrl:
            return None
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
        broadcasts = self.makeArray(pyUtils.extractJsonValue(data, 'data', 'search', 'programSets','nodes'))
        for broadcast in broadcasts:
            rs.append([pyUtils.extractJsonValue(broadcast, 'id'), pyUtils.extractJsonValue(broadcast, 'title'), pyUtils.extractJsonValue(broadcast, 'image', 'url')])
                
        #
        episodes = self.makeArray(pyUtils.extractJsonValue(data, 'data', 'search', 'items','nodes'))
        for episode in episodes:
            rs.append(
                [pyUtils.extractJsonValue(episode, 'id'),
                 pyUtils.extractJsonValue(episode, 'title'),
                 self._templateImages(pyUtils.extractJsonValue(episode, 'image', 'url')),
                 pyUtils.extractJsonValue(episode, 'audios', 0, 'url'),
                 pyUtils.extractJsonValue(episode, 'duration'),
                 self._parseTimestamp(pyUtils.extractJsonValue(episode, 'publishDate')),
                 pyUtils.extractJsonValue(episode, 'synopsis')]
            )
        #
        return rs

    # sometimes arrays are elements insteada of arrays
    def makeArray(self, element):
        elementArray = []
        if not element:
            return elementArray
        if isinstance(element, list):
            elementArray = element
        else:
            elementArray.append(element)
        return elementArray
