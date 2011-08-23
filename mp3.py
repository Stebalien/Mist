#!/usr/bin/python

import mutagen.id3
import mutagen.mp3

import jallen.dictools as dictools
import tagtools

encodings = {
    0: 'ISO-8859-1',
    1: 'UTF-16',
    2: 'UTF-16BE',
    3: 'UTF-8'
}

frames = {
    'RELATIVEVOLUME': ["RVA2", mutagen.id3.RVA2, ('text',), 3],
    'PLAYCOUNT':    ["PCNT", mutagen.id3.PCNT,('text',), 3],
    'DATE': ["TDRC", mutagen.id3.TDRC, ('text',),3],
    'ALBUM':        ['TALB',mutagen.id3.TALB, ('text',), 3],
    'BPM':          ['TBPM',mutagen.id3.TBPM, ('text',), 0],
    'COMPOSER':     ['TCOM',mutagen.id3.TCOM, ('text',), 3],
    'GENRE':        ['TCON',mutagen.id3.TCON, ('text',), 3],
    'COPYRIGHT':    ['TCOP',mutagen.id3.TCOP, ('text',), 3],
    'ENCODEDBY':    ['TENC',mutagen.id3.TENC, ('text',), 3],
    'LYRICIST':     ['TEXT',mutagen.id3.TEXT, ('text',), 3],
    'FILETYPE':     ['TFLT',mutagen.id3.TFLT, ('text',), 3],
    'INVOLVEDPEOPLE':   ['TIPL',mutagen.id3.TIPL, ('text',), 3],
    'CONTENTGROUP': ['TIT1',mutagen.id3.TIT1, ('text',), 3],
    'TITLE':        ['TIT2',mutagen.id3.TIT2, ('text',), 3],
    'SUBTITLE':     ['TIT3',mutagen.id3.TIT3, ('text',), 3],
    'INITIALKEY':   ['TKEY',mutagen.id3.TKEY, ('text',), 3],
    'LANGUAGE':     ['TLAN',mutagen.id3.TLAN, ('text',), 3],
    'LENGTH':       ['TLEN',mutagen.id3.TLEN, ('text',), 0],
    'MUSICIANCREDITS':  ['TMCL',mutagen.id3.TMCL, ('text',), 3],
    'MEDIATYPE':    ['TMED',mutagen.id3.TMED, ('text',), 3],
    'MOOD':         ['TMOO',mutagen.id3.TMOO, ('text',), 3],
    'ORIGALBUM':    ['TOAL',mutagen.id3.TOAL, ('text',), 3],
    'ORIGFILENAME': ['TOFN',mutagen.id3.TOFN, ('text',), 3],
    'ORIGLYRICIST': ['TOLY',mutagen.id3.TOLY, ('text',), 3],
    'ORIGARTIST':   ['TOPE',mutagen.id3.TOPE, ('text',), 3],
    'FILEOWNER':    ['TOWN',mutagen.id3.TOWN, ('text',), 3],
    'ARTIST':       ['TPE1',mutagen.id3.TPE1, ('text',), 3],
    'BAND':         ['TPE2',mutagen.id3.TPE2, ('text',), 3],
    'CONDUCTOR':    ['TPE3',mutagen.id3.TPE3, ('text',), 3],
    'MIXARTIST':    ['TPE4',mutagen.id3.TPE4, ('text',), 3],
    'DISCNUMBER':   ['TPOS',mutagen.id3.TPOS, ('text',), 0],
    'PUBLISHER':    ['TPUB',mutagen.id3.TPUB, ('text',), 3],
    'TRACK':        ['TRCK',mutagen.id3.TRCK, ('text',),0],
    'NETRADIOSTATION':  ['TRSN',mutagen.id3.TRSN, ('text',), 3],
    'NETRADIOOWNER':    ['TRSO',mutagen.id3.TRSO, ('text',), 3],
    'BANDSORTORDER':    ['TSO2',mutagen.id3.TSO2, ('text',), 3],
    'ALBUMSORTORDER':   ['TSOA',mutagen.id3.TSOA, ('text',), 3],
    'COMPOSERSORTORDER':['TSOC',mutagen.id3.TSOC, ('text',), 3],
    'ARTISTSORTORDER':   ['TSOP',mutagen.id3.TSOP, ('text',), 3],
    'TITLESORTORDER':   ['TSOT', mutagen.id3.TSOT, ('text',), 3],
    'ISRC':         ['TSRC',mutagen.id3.TSRC, ('text',), 3],
    'ENCODERSETTINGS':  ['TSSE',mutagen.id3.TSSE, ('text',), 3],
    'SETSUBTITLE':  ['TSST',mutagen.id3.TSST, ('text',), 3],
    'SONGID': [u'TXXX',mutagen.id3.TXXX, ('desc', 'text'), 3, "MLibrary_$USERID$_ID"],
    'PRIVATE':  ['PRIV',mutagen.id3.PRIV, ('text',), 3]
}


class Tag(tagtools.Tag):
    def __init__(self,filename,user_id=None):
        tagtools.Tag.__init__(self,filename,user_id)

    def read(self,details=[],ignore=[],force=False):
        failed = []
        data = {}
        if details ==[]:
            details = frames.keys()
        details = [x.upper() for x in details]
        try: mutagen_tag = mutagen.id3.ID3(self.filename)
        except:
            data = {}
            if force:
                for item in details:
                    data[item] = ""
            return data, details

        for ignore_item in ignore:
            details.remove(ignore_item.upper())
        for item in details:
            try:
                frame = frames[item][0]
                if frame == u'TXXX':
                    user_frame = frames[item][4].replace('$LIBRARYID$', str(self.user_id))
                    frame = unicode(frame + ":" + user_frame)
                data[item] = self.trunc_list(mutagen_tag[frame])
            except KeyError:
                failed.append(item)
                if force:
                    data[item] = ""
        return data, failed


    def write(self,data):

        failed = []
        data = dictools.make_keys_upper(data)

        try:
            mutagen_tag  = mutagen.id3.ID3(self.filename)
            new_tag = False
        except:
            new_tag = True
            mutagen_tag = mutagen.id3.ID3()

        for item in data.keys():
            try:
                frame = frames[item]
                encoding = frame[3]
                args = []
                for argument in frame[2]:
                    if argument == 'text':
                        args.append("text=\'{0}\'".format(unicode(str(data[item])), encodings[encoding]))
                    if argument == 'desc':
                        user_frame = frames[item][4].replace('$LIBRARYID$', str(self.user_id))
                        args.append("desc=\'{0}\'".format(unicode(user_frame)))
                    if argument == 'lang':
                        args.append("lang=\'{0}\'".format(unicode("eng")))
                code = "mutagen_tag.add(mutagen.id3." + frame[0] + "(encoding="+str(encoding)
                for argument in args:
                    code += ", "+argument
                code += "))"
                exec(code)
                if not new_tag:
                    mutagen_tag.save()
                else:
                    mutagen_tag.save(self.filename)
            except KeyError:
                failed.append(item)
        return failed
