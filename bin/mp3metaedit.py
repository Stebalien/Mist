"""
MP3 metadata formats for metaedit module
"""

__author__ = "jonathan"
__all__ = ["MP3_TAG_NAMES", "MP3Metadata"]


from jonathan.dictools import *
from metaedit import *

#===============================================================================
# Import Mutagen Modules
#===============================================================================
import mutagen.id3 as _id3

#===============================================================================
# Tag Formats
#===============================================================================
_ENCODINGS = {
    0: "ISO - 8859 - 1",
    1: "UTF - 16",
    2: "UTF - 16BE",
    3: "UTF - 8"
}

MP3_TAG_NAMES = {
    "RELATIVEVOLUME": ["RVA2", _id3.RVA2, ("text",), 3],
    "PLAYCOUNT":    ["PCNT", _id3.PCNT, ("text",), 3],
    "DATE": ["TDRC", _id3.TDRC, ("text",), 3],
    "ALBUM":        ["TALB", _id3.TALB, ("text",), 3],
    "BPM":          ["TBPM", _id3.TBPM, ("text",), 0],
    "COMPOSER":     ["TCOM", _id3.TCOM, ("text",), 3],
    "GENRE":        ["TCON", _id3.TCON, ("text",), 3],
    "COPYRIGHT":    ["TCOP", _id3.TCOP, ("text",), 3],
    "ENCODEDBY":    ["TENC", _id3.TENC, ("text",), 3],
    "LYRICIST":     ["TEXT", _id3.TEXT, ("text",), 3],
    "FILETYPE":     ["TFLT", _id3.TFLT, ("text",), 3],
    "INVOLVEDPEOPLE":   ["TIPL", _id3.TIPL, ("text",), 3],
    "CONTENTGROUP": ["TIT1", _id3.TIT1, ("text",), 3],
    "TITLE":        ["TIT2", _id3.TIT2, ("text",), 3],
    "SUBTITLE":     ["TIT3", _id3.TIT3, ("text",), 3],
    "INITIALKEY":   ["TKEY", _id3.TKEY, ("text",), 3],
    "LANGUAGE":     ["TLAN", _id3.TLAN, ("text",), 3],
    "LENGTH":       ["TLEN", _id3.TLEN, ("text",), 0],
    "MUSICIANCREDITS":  ["TMCL", _id3.TMCL, ("text",), 3],
    "MEDIATYPE":    ["TMED", _id3.TMED, ("text",), 3],
    "MOOD":         ["TMOO", _id3.TMOO, ("text",), 3],
    "ORIGALBUM":    ["TOAL", _id3.TOAL, ("text",), 3],
    "ORIGFILENAME": ["TOFN", _id3.TOFN, ("text",), 3],
    "ORIGLYRICIST": ["TOLY", _id3.TOLY, ("text",), 3],
    "ORIGARTIST":   ["TOPE", _id3.TOPE, ("text",), 3],
    "FILEOWNER":    ["TOWN", _id3.TOWN, ("text",), 3],
    "ARTIST":       ["TPE1", _id3.TPE1, ("text",), 3],
    "BAND":         ["TPE2", _id3.TPE2, ("text",), 3],
    "CONDUCTOR":    ["TPE3", _id3.TPE3, ("text",), 3],
    "MIXARTIST":    ["TPE4", _id3.TPE4, ("text",), 3],
    "DISCNUMBER":   ["TPOS", _id3.TPOS, ("text",), 0],
    "PUBLISHER":    ["TPUB", _id3.TPUB, ("text",), 3],
    "TRACK":        ["TRCK", _id3.TRCK, ("text",), 0],
    "NETRADIOSTATION":  ["TRSN", _id3.TRSN, ("text",), 3],
    "NETRADIOOWNER":    ["TRSO", _id3.TRSO, ("text",), 3],
    "BANDSORTORDER":    ["TSO2", _id3.TSO2, ("text",), 3],
    "ALBUMSORTORDER":   ["TSOA", _id3.TSOA, ("text",), 3],
    "COMPOSERSORTORDER":["TSOC", _id3.TSOC, ("text",), 3],
    "ARTISTSORTORDER":   ["TSOP", _id3.TSOP, ("text",), 3],
    "TITLESORTORDER":   ["TSOT", _id3.TSOT, ("text",), 3],
    "ISRC":         ["TSRC", _id3.TSRC, ("text",), 3],
    "ENCODERSETTINGS":  ["TSSE", _id3.TSSE, ("text",), 3],
    "SETSUBTITLE":  ["TSST", _id3.TSST, ("text",), 3],
    "SONGID": [u"TXXX", _id3.TXXX, ("desc", "text"), 3, "Mist"],
    "PRIVATE":  ["PRIV", _id3.PRIV, ("text",), 3]
}


class MP3Metadata(Metadata):
    def __init__(self, fileName):
        Metadata.__init__(self, fileName)
        self.failedReads

    @EncodeOutput
    def read(self, tagNames = [], ignoreTags = []):
        self.failedReads.difference_update(set(tagNames))
        tagNames = [tagName.upper() for tagName in tagNames]
        ignoreTags = [ignoreTag.upper() for ignoreTag in ignoreTags]

        if tagNames == []:
            tagNames = MP3_TAG_NAMES.keys()

        tagNames = set(tagNames)
        tagNames.difference_update(set(ignoreTags))

        [self.data.__setitem__(tagName, None) for tagName in tagNames]

        try: mutagenHandler = _id3.ID3(self.fileName)
        except: raise UnsupportedFiletypeError("cannot read metadata for file: <{}>.".format(self.fileName))

        for tagName in tagNames:
            try:
                formattedTagName = MP3_TAG_NAMES[tagName][0]
                if formattedTagName == u"TXXX":
                    formattedTagName = unicode(formattedTagName + ":Mist")
                self.data[tagName] = self.truncateOutput(mutagenHandler[formattedTagName])
            except KeyError:
                self.failedReads.add(tagName)
        return self.data

    def write(self, data):
        self.data.keysUpper()
        self.failedWrites.difference_update(set(data.keys()))

        try:
            mutagenHandler = _id3.ID3(self.fileName)
            newMetadata = False
        except:
            newMetadata = True
            mutagenHandler = _id3.ID3()

        for tagName in data.keys():
            try:
                tagFormat = MP3_TAG_NAMES[tagName]
                encoding = tagFormat[3]
                mutagenArguments = []
                for argument in tagFormat[2]:
                    if argument == "text":
                        mutagenArguments.append("text = \"{0}\"" \
                                                .format(unicode(str(data[tagName])), \
                                                        _ENCODINGS[encoding]))
                    if argument == "desc":
                        userFrame = tagFormat[4]
                        mutagenArguments.append("desc=\"{0}\"" \
                                                .format(unicode(userFrame)))
                    if argument == "lang":
                        mutagenArguments.append("lang=\"{0}\"" \
                                                .format(unicode("eng")))
                command = "mutagenHandler.add(_id3." + tagFormat[0] \
                            + "(encoding=" + str(encoding)
                for argument in mutagenArguments:
                    command += ", " + argument
                command += "))"
                exec(command)
                if not newMetadata: mutagenHandler.save()
                else: mutagenHandler.save(self.fileName)
            except KeyError:
                self.failedWrites.add(tagName)
