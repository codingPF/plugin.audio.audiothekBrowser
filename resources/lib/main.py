# -*- coding: utf-8 -*-
"""
The main addon module

SPDX-License-Identifier: MIT

"""
import time
import resources.lib.appContext as appContext
import resources.lib.utils as pyUtils
import resources.lib.ui.mainMenuUi as MainMenuUI
import resources.lib.ui.listUi as ListUI
import resources.lib.ui.episodeUi as EpisodeUI
import resources.lib.ui.livestreamUi as LivesreamUI
import resources.lib.sqliteDB as SqliteDb
from resources.lib.refresh import Refresh
from resources.lib.kodi import Kodi
import resources.lib.kodiProgressDialog as PG
#


class Main(Kodi):

    def __init__(self):
        super(Main, self).__init__()
        self.logger = appContext.LOGGER.getInstance('MAIN')
        self.settings = appContext.SETTINGS
        # ensure we have settings and a addon data directory
        self.setSetting('lastUsed', str(int(time.time())))
        #
        self.db = SqliteDb.SqliteDB(pyUtils.createPath((self.getAddonDataPath(), 'audiothekDB.db')))
        # print(datetime.datetime.strptime("21/11/06 16:30", "%d/%m/%y %H:%M"))
        # print(str(pyUtils.epoch_from_timestamp('2020-11-07T16:12:13.987+0100', '%Y-%m-%dT%H:%M:%S.%f%z')))
        self.refresh = Refresh(self.db)
        self.refresh.run()
        #

    def run(self):
        #
        mode = self.getParameters('mode')
        parameterId = self.getParameters('id')
        self.logger.info('Run Plugin with Parameters {}', self.getParameters())
        if mode == 'organization':
            mmUI = ListUI.ListUI(self, 'channel')
            mmUI.generate(self.db.getOrganizations())
        elif mode == 'channel':
            mmUI = ListUI.ListUI(self, 'broadcast')
            mmUI.generate(self.db.getChannel(parameterId))
        elif mode == 'broadcast':
            mmUI = ListUI.ListUI(self, 'episode')
            mmUI.generate(self.db.getBroadcast(parameterId))
        elif mode == 'episode':
            kpg = PG.KodiProgressDialog()
            kpg.startBussyDialog()
            self.refresh.loadEpisode(parameterId)
            mmUI = EpisodeUI.EpisodeUI(self)
            mmUI.generate(self.db.getEpisodes(parameterId))
            kpg.stopBussyDialog()
        elif mode == 'livestream':
            mmUI = LivesreamUI.LivestreamUI(self)
            mmUI.generate(self.db.getLivestream())
        elif mode == 'download':
            kodiPG = PG.KodiProgressDialog()
            kodiPG.create(30102)
            #
            rs = self.db.getEpisode(parameterId)
            url = rs[0][5]
            name = rs[0][1]
            name = pyUtils.file_cleanupname(name)
            fullName = pyUtils.createPath((self.translatePath(self.settings.getDownloadPath()), name))
            pyUtils.url_retrieve(url, fullName, reporthook=kodiPG.update, chunk_size=65536, aborthook=self.getAbortHook())
            #
            kodiPG.close()
            #
        elif mode == 'refresh':
            self.db.reset()
            self.executebuiltin('Container.Refresh')
        else:
            mmUI = MainMenuUI.MainMenuUI(self)
            mmUI.generate()
        #
        self.db.exit()
