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
from resources.lib.refreshArdAudiothek import RefreshArdAudiothek
from resources.lib.refreshSrfAudiothek import RefreshSrfAudiothek

class Refresh(object):
    """
    Refresh

    """

    def __init__(self, pDb):
        self.logger = appContext.LOGGER.getInstance('Refresh')
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
        if not(self.db.isInitialized()):
            self.settings.setLastUpdateIndex('0')
            self.db.create()
        #
        age = int((time.time() - self.settings.getLastUpdateIndex()) / 60)
        if age < self.settings.getUpdateInterval():
            self.logger.debug('Index is up-to-date age: {} / {}', age, self.settings.getUpdateInterval())
            return
        else:
            self.logger.debug('Update index due to age: {} / {} last {} cTime {}', age, self.settings.getUpdateInterval(), self.settings.getLastUpdateIndex(), int(time.time()))
        #
        self.db.deleteShows();
        self.db.deleteLivestream();
        #
        ard = RefreshArdAudiothek(self.db)
        ard.run()
        #
        srf = RefreshSrfAudiothek(self.db)
        srf.run()
        #
        self.settings.setLastUpdateIndex(str(int(time.time())))
        self.logger.info('last update {} vs {}', str(int(time.time())), self.settings.getLastUpdateIndex())
        #

    def loadEpisode(self, parameterId):
        #
        if parameterId.startswith('urn:srf'):
            srf = RefreshSrfAudiothek(self.db)
            srf.loadEpisode(parameterId)
        else:
            ard = RefreshArdAudiothek(self.db)
            ard.loadEpisode(parameterId)
        #
        
    
    def loadVideoFile(self):
        #
        None
