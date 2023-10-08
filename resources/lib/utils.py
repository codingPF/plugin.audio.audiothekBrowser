# -*- coding: utf-8 -*-
"""
Utilities module
SPDX-License-Identifier: MIT
"""

import os
import sys
import stat
import re
import string
import json
import datetime
import time
import base64
from contextlib import closing
from codecs import open
try:
    # Python 3.x
    from urllib.parse import urlencode
    from urllib.request import urlopen
except ImportError:
    from urllib import urlencode
    from urllib2 import urlopen

#########################################################################
# PYTHON 2 / 3 madness
#########################################################################
PY2 = sys.version_info[0] == 2


def py2_encode(s, encoding='utf-8'):
    """
    Encode Python 2 ``unicode`` to ``str``

    In Python 3 the string is not changed.   
    """
    if PY2 and isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def py2_decode(s, encoding='utf-8'):
    """
    Decode Python 2 ``str`` to ``unicode``

    In Python 3 the string is not changed.
    """
    if PY2 and isinstance(s, str):
        s = s.decode(encoding)
    return s


def array_to_utf(a):
    """ Build a new array and encode all elements """
    autf = []
    for v in a:
        if PY2 and isinstance(v, unicode):
            autf.append(py2_encode(v))
        elif PY2 and isinstance(v, dict):
            autf.append(dict_to_utf(v))
        elif PY2 and isinstance(v, list):
            autf.append(array_to_utf(v))
        else:
            autf.append(v)
    return autf


def dict_to_utf(d):
    """ Build a new dict and encode all elements """
    dutf = {}
    for k, v in list(d.items()):
        if PY2 and isinstance(v, unicode):
            dutf[k] = py2_encode(v)
        elif PY2 and isinstance(v, list):
            dutf[k] = array_to_utf(v)
        elif PY2 and isinstance(v, dict):
            dutf[k] = dict_to_utf(v)
        else:
            dutf[k] = v
    return dutf


#########################################
# EPOCH FROM TZ
#
def epoch_from_timestamp(pTimestampString, pTsPatter='%Y-%m-%dT%H:%M:%S.%f%z'):
    new_time = datetime.datetime.strptime(pTimestampString, pTsPatter)
    return int(new_time.timestamp())

def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset
    
#########################################################################
# FILE functions


def createPath(params):
    return os.path.join(*params)


def dir_exists(name):
    """
    Tests if a directory exists

    Args:
        name(str): full pathname of the directory
    """
    try:
        state = os.stat(name)
        return stat.S_ISDIR(state.st_mode)
    except OSError:
        return False


def file_exists(name):
    """
    Tests if a file exists

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return stat.S_ISREG(state.st_mode)
    except OSError:
        return False


def file_size(name):
    """
    Get the size of a file

    Args:
        name(str): full pathname of the file
    """
    try:
        state = os.stat(name)
        return state.st_size
    except OSError:
        return 0


def file_remove(name):
    """
    Delete a file

    Args:
        name(str): full pathname of the file
    """
    if file_exists(name):
        try:
            os.remove(name)
            return True
        except OSError:
            pass
    return False


def file_rename(srcname, dstname):
    """
    Rename a file

    Args:
        srcname(str): name of the source file
        dstname(str): name of the file after the rename operation
    """
    if file_exists(srcname):
        try:
            os.rename(srcname, dstname)
            return True
        except OSError:
            # maybe windows on overwrite. try non atomic rename
            try:
                os.remove(dstname)
                os.rename(srcname, dstname)
                return True
            except OSError:
                return False
    return False


def file_cleanupname(val):
    """
    Strips strange characters from a string in order
    to create a valid filename

    Args:
        val(str): input string
    """
    cStr = val.strip().replace(' ', '_')
    cStr = re.sub(r'(?u)[^-\w.]', '', cStr)
    return cStr

def extractJsonValue(rootElement, *args):
    if rootElement is None:
        return None
    #
    root = rootElement;
    for searchPath in args:
        if isinstance(root, list):
            if len(root) > searchPath:
                root = root[searchPath]
            else:
                return None
        else:
            if searchPath in root:
                root = root.get(searchPath)
            else:
                return None
    return root;
    
#########################################################################################


def loadJson(filename):
    with closing(open(filename, encoding='utf-8')) as json_file:
        data = json.load(json_file)
    return data


def saveJson(filename, data):
    with closing(open(filename, 'w', encoding='utf-8')) as json_file:
        json.dump(cache, json_file)

##########################################################################################


def b64encode(pMessage):
    message_bytes = pMessage.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message


def b64decode(pMessage):
    base64_bytes = pMessage.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
    return message

###########################################################################################

def url_to_string(url, chunk_size=65536):
    output = ''
    with closing(urlopen(url, timeout=10)) as src:
        while True:
            byteStringchunk = src.read(chunk_size)
            if not byteStringchunk:
                # operation has finished
                break
            output += byteStringchunk
            # abort requested
    return output


def url_retrieve(url, filename, reporthook=None, chunk_size=65536, aborthook=None):
    """
    Copy a network object denoted by a URL to a local file

    Args:
        url(str): the source url of the object to retrieve

        filename(str): the destination filename

        reporthook(function): a hook function that will be called once on
            establishment of the network connection and once after each
            block read thereafter. The hook will be passed three arguments;
            a count of blocks transferred so far, a block size in bytes,
            and the total size of the file.

        chunk_size(int, optional): size of the chunks read by the function.
            Default is 8192

        aborthook(function, optional): a hook function that will be called
            once on establishment of the network connection and once after
            each block read thereafter. If specified the operation will be
            aborted if the hook function returns `True`
    """
    with closing(urlopen(url, timeout=10)) as src, closing(open(filename, 'wb')) as dst:
        _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook)


def build_url(query):
    """
    Builds a valid plugin url based on the supplied query object

    Args:
        query(object): a query object
    """
    utfEnsuredParams = dict_to_utf(query)
    return sys.argv[0] + '?' + urlencode(utfEnsuredParams)

def build_external_url(pHost, pQuery):
    """
    Builds a valid plugin url based on the supplied query object

    Args:
        query(object): a query object
    """
    utfEnsuredParams = dict_to_utf(pQuery)
    return pHost + '?' + urlencode(utfEnsuredParams)

def _chunked_url_copier(src, dst, reporthook, chunk_size, aborthook):
    aborthook = aborthook if aborthook is not None else lambda: False
    reporthook = reporthook if reporthook is not None else lambda p: True
    total_size = int(
        src.info().get('Content-Length').strip()
    ) if src.info() and src.info().get('Content-Length') else 0
    total_chunks = 0
    if total_size < 1:
        total_size = 1

    while not aborthook():
        reporthook(int(((total_chunks * chunk_size) * 100) / total_size))
        byteStringchunk = src.read(chunk_size)
        if not byteStringchunk:
            # operation has finished
            return
        dst.write(bytearray(byteStringchunk))
        total_chunks += 1
    # abort requested
    raise Exception('Reception interrupted.')

