"""Metadata formats for metaedit module."""

__author__ = "jonathan"
__all__ = ["STANDARD_TAG_NAMES", "M4A_TAG_NAMES", "StandardMetadata"]

from metaedit import *
import jonathan.ltools as ltools
from jonathan.dictools import *

#===============================================================================
# Tag Formats
#===============================================================================
STANDARD_TAG_NAMES = {
					"TITLE": "title",
					"ALBUM": "album",
					"ARTIST": "artist",
					"ARTISTSORTORDER": "albumartistsort",
					"PRODUCER": "producer",
					"VERSION": "version",
					"TRACKNUMBER": "tracknumber",
					"PERFORMER": "performer",
					"RECORDINGLABEL":"label",
					"DATE":"date",
					"GENRE": "genre",
					"DATE": "date"
					}

M4A_TAG_NAMES = {
				"TITLE": b"\xa9nam",
				"ALBUM": b"\xa9alb",
				"COMPOSER": b"\xa9wrt",
				"COMMENT": b"\xa9cmt",
				"ART": b"covr",
				"GENRE": b"\xa9gen",
				"ARTIST": b"\xa9ART",
				"RECORDINGTIME": b"\xa9day",
				"DISK": b"disk",
				"TRACK": b"trkn",
				"LENGTH": None,
				"BITRATE": None,
				"ALBUMSORTORDER": b"soal",
				"ARTISTSORTORDER": b"soar",
				"TITLESORTORDER": b"sonm",
				"BPM": b"tmpo",
				"PLAYCOUNT": b"plcnt",
				"RELATIVEVOLUME": b"RVA",
				"SONGID": b"----:com.apple.iTunes:MLibrary_$LIBRARYID$"
				}

#===============================================================================
# Import Mutagen Modules
#===============================================================================
from mutagen.oggvorbis import OggVorbis as _OggVorbis
from mutagen.flac import FLAC as _FLAC
from mutagen.m4a import M4A as _M4A

_MUTAGEN_MODULES = {
    "audio/ogg": _OggVorbis,
    "audio/flac": _FLAC,
    "audio/mp4": _M4A
}


class StandardMetadata(Metadata):
	"""
	Class to handle metadata for filetypes in _MUTAGEN_MODULES. This class is usually
	called indirectly through the metaedit.Metadata class.
	"""
	def __init__(self, fileName):
		Metadata.__init__(self, fileName)
		self.tagNames = STANDARD_TAG_NAMES

		if self.fileType == 'audio/mp4':
			self.tagNames = M4A_TAG_NAMES

	@EncodeOutput
	def read(self, tagNames = [], ignore = []):
		self.failedReads.difference_update(set(tagNames))
		tagNames = ltools.upper(tagNames)
		ignore = ltools.upper(ignore)

		if tagNames == []:
			tagNames = self.tagNames.keys()

		tagNames = set(tagNames)
		tagNames.difference_update(set(ignore))

		[self.data.__setitem__(tagName, None) for tagName in tagNames]

		try: mutagenHandler = _MUTAGEN_MODULES[self.fileType](self.fileName)
		except: raise UnsupportedFiletypeError("cannot read metadata for file: <{}>.".format(self.fileName))

		for tagName in tagNames:
			try:
				formattedTagName = self.tagNames[tagName]
				self.data[tagName] = self.truncateOutput(mutagenHandler[formattedTagName])
			except KeyError:
				self.failedReads.add(tagName)
		return self.data

	def write(self, data):
		data.keysUpper()
		self.failedWrites.difference_update(set(data.keys()))

		try:
			mutagenHandler = _MUTAGEN_MODULES[self.fileType](self.fileName)
			newMetadata = False
		except:
			newMetadata = True
			mutagenHandler = _MUTAGEN_MODULES[self.fileType](self.fileName)

		for tagName in data.keys():
			try:
				formattedTagName = self.tagNames[tagName]
				mutagenHandler[formattedTagName] = unicode(data[tagName])
				if not newMetadata: mutagenHandler.save()
				else: mutagenHandler.save(self.fileName)
			except KeyError:
				self.failedWrites.add(tagName)

	def removeTag(self, tagName):
		try:
			mutagenHandler = _MUTAGEN_MODULES[self.fileType](self.fileName)
			formattedTagName = self.tagNames[tagName]
			del mutagenHandler[formattedTagName]
			mutagenHandler.save()
		except KeyError:
			pass





