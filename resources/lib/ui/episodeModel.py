'''
Created on 25.01.2021

@author: steph
'''


class EpisodeModel(object):

    def __init__(self):
        self.id = 0
        self.title = ''
        self.duration = ''
        self.aired = 0
        self.description = ''
        self.url = ''
        self.image = ''
        self.created = 0

    def init(self, pId, pTitle, pDuration, pAired, pDescription, pUrl, pImage, pCreated):
        self.id = pId
        self.title = pTitle
        self.duration = pDuration
        self.aired = pAired
        self.description = pDescription
        self.url = pUrl
        self.image = pImage
        self.created = pCreated
