'''
Created on 25.01.2021

@author: steph
'''


class ListModel(object):

    def __init__(self):
        self.id = 0
        self.name = ''
        self.image = ''

    def init(self, pId, pName, pImage):
        self.id = pId
        self.name = pName
        self.image = pImage

