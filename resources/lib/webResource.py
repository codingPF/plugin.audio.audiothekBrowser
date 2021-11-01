# -*- coding: utf-8 -*-
"""
The local SQlite database module
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import resources.lib.appContext as appContext
import time
import traceback
#
import gzip
from contextlib import closing

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

    """

    def __init__(self, pUrl):
        self.logger = appContext.LOGGER.getInstance('WebResource')
        #
        self.userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0';
        #
        self.url = pUrl
        #

    def retrieveAsString(self):
        #
        starttime = time.time()
        #
        request = Request(self.url)
        request.add_header('Accept-encoding', 'gzip')
        request.add_header('User-Agent', self.userAgent)
        #
        try:
        #
            with closing(urlopen(request)) as response:
                #
                content_encoding = response.info().get('Content-Encoding')
                #
                self.logger.info('content type {} OR {}', content_encoding, response.headers.get('Content-Encoding'))
                # how to decompress gzip data with Python 3
                if PY2FOUND:
                    if content_encoding == 'gzip':
                        gz = gzip.GzipFile(fileobj=StringIO(response.read()))
                        outputString = gz.read()
                    else:
                        outputString = response.read()
                else:
                    if content_encoding == 'gzip':
                        gz = gzip.GzipFile(fileobj=BytesIO(response.read()))
                        outputString = gz.read()
                    else:
                        outputString = response.read()
        #
        except Exception as e:
            self.logger.error('WebResource exception {} code {}', self.url, traceback.format_exc())
            outputString = ''
    
        self.logger.debug('WebResource url {} retrieved in {} sec(s)',self.url, (time.time() - starttime))
        #
        return outputString
