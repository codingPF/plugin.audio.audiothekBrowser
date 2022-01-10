# -*- coding: utf-8 -*-
"""
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import resources.lib.appContext as appContext
#
import zlib
#
from contextlib import closing
#
try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
    from io import BytesIO
    # from io import StringIO
    PY2FOUND = False
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError
    from cStringIO import StringIO
    PY2FOUND = True


class WebResource(object):
    """
    Download url
    
    
    to (de-)compress deflate format, use wbits = -zlib.MAX_WBITS
    to (de-)compress zlib format, use wbits = zlib.MAX_WBITS
    to (de-)compress gzip format, use wbits = zlib.MAX_WBITS | 16

    """

    def __init__(self, pUrl, pHeader = None, pAbortHook = None, pProgressListener = None, pChunkSize=8192, pTimeout=10):
        self.logger = appContext.LOGGER.getInstance('WebResource')
        #
        self.abortHook = pAbortHook if pAbortHook else lambda: False
        #
        self.progressListener = pProgressListener if pProgressListener else self._progressListener
        #
        self.connectionTimeout = pTimeout
        #
        self.chunkSize = pChunkSize
        #
        if pHeader == None:
            self.header = {
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
                'Accept-encoding': 'gzip'
            }
        else:
            self.header = pHeader    
        #
        self.url = pUrl
        #

    def retrieveAsString(self):
        #
        request = Request(self.url)
        #
        for kkey,vvalue in list(self.header.items()):
            request.add_header(kkey, vvalue)
        #
        rsArrayBuffer = []
        #
        with closing(urlopen(request, timeout=self.connectionTimeout)) as response:
            #
            content_encoding = response.info().get('Content-Encoding')
            self.logger.debug('content_encoding {}', content_encoding )
            #
            content_length = response.info().get("Content-Length")
            content_length = int(content_length) if content_length else self.chunkSize*100
            self.logger.debug('content_length {}',content_length )
            #
            cycleCnt = 1
            #
            if content_encoding == 'gzip':
                decomp = zlib.decompressobj(16+zlib.MAX_WBITS)
            elif content_encoding == 'deflate':
                decomp = zlib.decompressobj(-zlib.MAX_WBITS)
            else:
                decomp = None
            #
            buffer=response.read(self.chunkSize)
            #
            while buffer and not self.abortHook():
                if decomp:
                    outstr = decomp.decompress(buffer)
                else:
                    outstr = buffer
                #
                rsArrayBuffer.append(outstr)
                buffer=response.read(self.chunkSize)
                cycleCnt += 1
                self.progressListener(cycleCnt*self.chunkSize, content_length)
            #
            if decomp:
                outstr = decomp.flush()
                rsArrayBuffer.append(outstr)
            #
            outputString = b''.join(rsArrayBuffer)
            #
        return outputString
            
    def _progressListener(self, pDone, pTotal):
        pass
