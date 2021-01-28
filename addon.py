# -*- coding: utf-8 -*-
"""
The main addon module

SPDX-License-Identifier: MIT

"""

# -- Imports ------------------------------------------------
import xbmcaddon
import resources.lib.appContext as appContext
import resources.lib.settings as Settings
import resources.lib.logger as Logger
import resources.lib.main as Main

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    appContext.init()
    appContext.initAddon(xbmcaddon.Addon())
    appContext.initLogger(Logger.Logger(appContext.ADDONCLASS.getAddonInfo('id'), appContext.ADDONCLASS.getAddonInfo('version')))
    appContext.initSettings(Settings.Settings(appContext.ADDONCLASS))
    PLUGIN = Main.Main()
    PLUGIN.run()
    del PLUGIN
