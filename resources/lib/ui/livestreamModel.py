'''
Created on 25.01.2021

@author: steph
'''


class LivestreamModel(object):

    def __init__(self):
        self.id = 0
        self.title = ''
        self.image = ''
        self.url = ''
        self.description = ''

    def init(self, pId, pTitle, pImage, pUrl, pDescription):
        self.id = pId
        self.title = pTitle
        self.image = pImage
        self.url = pUrl
        self.description = pDescription

