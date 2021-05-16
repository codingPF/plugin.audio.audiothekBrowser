# -*- coding: utf-8 -*-
"""
The addon settings module
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import xbmc
import xbmcvfs
import resources.lib.utils as pyUtiles
# -- Classes ------------------------------------------------


class Settings(object):
    """ The settings class """

    def __init__(self, pAddonClass):
        xbmc.log("SettingsKodi:init", xbmc.LOGDEBUG)
        self._addonClass = pAddonClass
        pass

    # self.datapath
    def getDatapath(self):
        if self.getKodiVersion() > 18:
            return pyUtiles.py2_decode(xbmcvfs.translatePath(self._addonClass.getAddonInfo('profile')))
        else:
            return pyUtiles.py2_decode(xbmc.translatePath(self._addonClass.getAddonInfo('profile')))

    def getKodiVersion(self):
        """
        Get Kodi major version
        Returns:
            int: Kodi major version (e.g. 18)
        """
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        return int(xbmc_version.split('-')[0].split('.')[0])

    # General
    def getIconSize(self):
        return self._addonClass.getSetting('iconSize')

    def getIconRatio(self):
        return self._addonClass.getSetting('iconRatio')

    def getLastUpdateIndex(self):
        try:
            return int(self._addonClass.getSetting('lastUpdateIndex'))
        except Exception:
            return 0

    def setLastUpdateIndex(self, pValue):
        self._addonClass.setSetting('lastUpdateIndex', pValue)

    def getUpdateInterval(self):
        return int(self._addonClass.getSetting('updateInterval'))

    def getDownloadPath(self):
        return self._addonClass.getSetting('downloadPath')
