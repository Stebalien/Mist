"""Metadata editor for Mist program. This is a wrapper class for the mutagen module."""

__author__ = "Jonathan Allen"
__all__ = ["FileError", "NonexistantFileError", "UnsupportedFiletypeError",
           "EncodeInput", "EncodeOutput", "Metadata", "GENERAL_TAGNAMES"]

import mimetypes
import os
import types

from jonathan.dictools import *

#===============================================================================
# Constants
#===============================================================================
GENERAL_TAGNAMES = ["TITLE", "ALBUM", "ARTIST", "ARTISTSORTORDER", "PRODUCER",
                    "PERFORMER", "RECORDINGLABEL", "DATE", "GENRE", "LOCATION"]

#===============================================================================
# Exceptions
#===============================================================================
class FileError(Exception):
    pass

class NonexistantFileError(FileError):
    pass

class UnsupportedFiletypeError(FileError):
    pass

#===============================================================================
# Decorators
#===============================================================================
def EncodeInput(function):
    """
    Encodes values in specified metadata as ASCII. Ignores invalid characters.
    """
    def wrapped(self, data):
        for key, value in data.items():
            try: value.decode('ascii')
            except UnicodeDecodeError:
                data[key] = value.encode('ascii', errors = 'ignore')
        return function(self, data)
    return wrapped

def EncodeOutput(function):
    """
    Encodes output metadata as ASCII. Ignores invalid characters.
    """
    def wrapped(*args, **kwargs):
        output = function(*args, **kwargs)
        for key, value in output.items():
            try: value.decode('ascii')
            except UnicodeDecodeError:
                try: output[key] = value.encode('ascii', errors = 'ignore')
                except: output[key] = "????"
        return output
    return wrapped


mimetypes.add_type('audio/mp4', '.m4a')

class Metadata:
    """
    Class to handle reading and writing metadata for music files.
    """
    def __init__(self, fileName):
        self.fileName = fileName
        self.fileType = mimetypes.guess_type(fileName)[0]
        self.data = ExtendedDictionary()
        self.failedReads = set()
        self.failedWrites = set()

    def __new__(cls, fileName):
        if not os.path.exists(fileName): raise NonexistantFileError("{} could not be found.".format(fileName))

        fileType = mimetypes.guess_type(fileName)[0]

        from mp3metaedit import MP3Metadata
        from standardmetaedit import StandardMetadata
        output = {
                  'audio/mpeg': MP3Metadata,
                  'audio/ogg': StandardMetadata,
                  'audio/flac': StandardMetadata,
                  'audio/mp4': StandardMetadata
        }
        try:
            return output[fileType](fileName)
        except KeyError:
            raise UnsupportedFiletypeError("cannot read metadata for filetype: <{}>.".format(fileType))

    @EncodeOutput
    def read(self, tagNames = [], ignore = []):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def truncateOutput(self, data):
        """
        If data is a list, returns the first value. Otherwise simply returns the given
        data.
        """
        if isinstance(data, (types.ListType, types.TupleType)):
            return bytes(data[0])
        return bytes(data)
