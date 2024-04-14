# -*- coding: utf-8 -*-
"""
The local SQlite database module
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import time
from ckfw import utils as pyUtils
from ckfw.sqliteDB import SqliteDB as SqliteDB

class DB(SqliteDB):
    """
    The local SQlite database class

    """

    def __init__(self, addon, databaseFilename):
        super(DB, self).__init__(addon, databaseFilename)
        self.logger = self.addon.createLogger('SqliteDB')
        self.logger.debug('DB File {}', self.databaseFilename)

    def isInitialized(self):
        rt = False
        try:
            sql = 'select 0 from audiofile where 1=0'
            rs = self.execute(sql, None)
            rt = True
        except Exception as err:
            pass
        return rt

    def create(self):
        self.execute("""
            CREATE TABLE category (
            organizationId INT, organizationName VARCHAR(32), organizationImage VARCHAR(128), 
            channelId INT, channelName VARCHAR(32), channelImage VARCHAR(128), 
            broadcastId INT NOT NULL PRIMARY KEY, broadcastName VARCHAR(32), broadcastImage VARCHAR(128),
            tags VARCHAR(256), tagImage VARCHAR(128))"""
                     , None)
        self.execute("""
            CREATE TABLE audiofile (
            broadcastId INT, episodeId INT NOT NULL PRIMARY KEY, episodeTitle VARCHAR(256),
            episodeDuration INT, episodeAired INT, episodeDescription VARCHAR(256), 
            episodeUrl VARCHAR(256), episodeImage VARCHAR(256), created INT)"""
                     , None)
        self.execute("""
            CREATE TABLE livestream (
            livestreamId INT NOT NULL PRIMARY KEY, livestreamName INT, livestreamImage VARCHAR(256), livestreamUrl VARCHAR(256), livestreamDescription VARCHAR(256))"""
                     , None)

    def setLastLoadEpisode(self, pBroadcast):
        sql = "update audiofile set created = ? where broadcastId = ?"
        rs = self.executeUpdate(sql, (int(time.time()), pBroadcast))
        return rs

    def getastLoadEpisode(self, pBroadcast):
        dt = 0
        sql = 'select max(created) from audiofile where broadcastId = ?'
        rs = self.execute(sql, (pBroadcast,))
        if (len(rs) > 0 and rs[0][0] != None):
            dt = int(rs[0][0])
        return dt

    def addEpisode(self, pKey, pParams):
        rs = 0
        deleteStmt = 'SELECT 1 FROM audiofile WHERE episodeId = ?'
        if len(self.execute(deleteStmt, (pKey,))) == 0:
            sql = "INSERT INTO audiofile values (?,?,?,?,?,?,?,?,?)"
            rs = self.executeUpdate(sql, pParams)
        return rs

    def deleteCategory(self):
        deleteStmt = "DELETE FROM category"
        return self.executeUpdate(deleteStmt, None)

    def deleteLivestream(self):
        deleteStmt = "DELETE FROM livestream"
        return self.executeUpdate(deleteStmt, None)

    def addCategory(self, pKey, pParams):
        rs = 0
        deleteStmt = 'SELECT 1 FROM category WHERE broadcastId = ?'
        if len(self.execute(deleteStmt, (pKey,))) == 0:
            sql = "INSERT INTO category values (?,?,?,?,?,?,?,?,?,?,?)"
            rs = self.executeUpdate(sql, pParams)
        return rs

    def addLivestream(self, pKey, pParams):
        rs = 0
        deleteStmt = 'SELECT 1 FROM livestream WHERE livestreamId = ?'
        if len(self.execute(deleteStmt, (pKey,))) == 0:
            sql = "INSERT INTO livestream values (?,?,?,?,?)"
            rs = self.executeUpdate(sql, pParams)
        return rs

####################################################

    def getLivestream(self):
        sql = "SELECT livestreamId, livestreamName, livestreamImage, livestreamUrl, livestreamDescription FROM livestream ORDER BY upper(livestreamName) asc"
        return self.execute(sql, None)

    def getOrganizations(self):
        sql = "SELECT organizationId, organizationName, organizationImage FROM category GROUP BY organizationId, organizationName, organizationImage ORDER BY upper(organizationName) asc"
        return self.execute(sql, None)

    def getChannel(self, pOrganizationId=None):
        params = []
        sql = "SELECT channelId, channelName, channelImage FROM category"
        if pOrganizationId != None:
            sql += " WHERE organizationId = ?"
            params.append(pOrganizationId)
        sql += " GROUP BY channelId, channelName, channelImage ORDER BY upper(channelName)"
        return self.execute(sql, params)

    def getBroadcast(self, pChannel=None):
        params = []
        sql = "SELECT broadcastId, broadcastName, broadcastImage FROM category"
        if pChannel != None:
            sql += " WHERE channelId = ?"
            params.append(pChannel)
        sql += ' ORDER BY upper(broadcastName)'
        return self.execute(sql, params)

    def getEpisodes(self, pBroadcast=None):
        params = []
        sql = "SELECT episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, created FROM audiofile"
        if pBroadcast != None:
            sql += " WHERE broadcastId = ?"
            params.append(pBroadcast)
        sql += ' ORDER BY episodeAired desc'
        return self.execute(sql, params)

    def getEpisode(self, pEpisodeId=None):
        params = []
        sql = "SELECT episodeId, episodeTitle, episodeDuration, episodeAired, episodeDescription, episodeUrl, episodeImage, created FROM audiofile WHERE episodeId = ? ORDER BY episodeTitle"
        params.append(pEpisodeId)
        return self.execute(sql, params)

    def getTags(self, pTags=None):
        params = []
        sql = "SELECT tags, tags, tagImage FROM category WHERE tags is not null"
        if pTags != None:
            sql += " AND tags = ?"
            params.append(pTags)
        sql +=  ' GROUP BY tags ORDER BY upper(tags)'
        return self.execute(sql, params)

    def getTag(self, pTags=None):
        params = []
        sql = "SELECT broadcastId, broadcastName, broadcastImage FROM category"
        if pTags != None:
            sql += " WHERE tags = ?"
            params.append(pTags)
        sql += ' ORDER BY upper(broadcastName)'
        return self.execute(sql, params)