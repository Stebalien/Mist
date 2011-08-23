#!/usr/bin/python

from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.m4a import M4A

import tagtools
import jallen.dictools as dictools

general_frames = {
	'TITLE': "title",
	'ALBUM': "album",
	'ARTIST': "artist",

        'ARTISTSORTORDER': "albumartistsort",
        'PRODUCER': "producer",
        'VERSION': "version",
        "TRACKNUMBER": "tracknumber",
        "PERFORMER": "performer",
        "RECORDINGLABEL":"label",
        "DATE":"date",
        "GENRE": "genre",
        "DATE": "date"
}

m4a_frames = {
    'TITLE': b"\xa9nam",
    'ALBUM': b"\xa9alb",
    'COMPOSER': b"\xa9wrt",
    'COMMENT':b"\xa9cmt",
    'ART':b"covr",
    'GENRE': b"\xa9gen",
    'ARTIST': b"\xa9ART",
    'RECORDINGTIME': b"\xa9day",
    'DISK': b"disk",
    'TRACK': b"trkn",
    'LENGTH': None,
    'BITRATE': None,
    'ALBUMSORTORDER': b"soal",
    'ARTISTSORTORDER': b"soar",
    'TITLESORTORDER': b"sonm",
    'BPM': b"tmpo",
    'PLAYCOUNT': b"plcnt",
    'RELATIVEVOLUME': b"RVA",
    'SONGID': b"----:com.apple.iTunes:MLibrary_$LIBRARYID$"
}

mutagen_modules = {
    'audio/ogg': OggVorbis,
    'audio/flac': FLAC,
    'audio/mp4': M4A
}

class Tag(tagtools.Tag):
    def __init__(self,filename,user_id=None):
        tagtools.Tag.__init__(self,filename,user_id)
        self.frames = general_frames
        if self.file_type == 'audio/mp4':
            self.frames = m4a_frames
   
    def read(self,details=[], ignore=[], force=False):
        failed = []
        if details ==[]:
            details = self.frames.keys()
        details = [x.upper() for x in details]
        data = {}
        try: mutagen_tag = mutagen_modules[self.file_type](self.filename)
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
                frame = self.frames[item]
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
            mutagen_tag = mutagen_modules[self.file_type](self.filename)
            new_tag = False
        except:
            new_tag = True
            mutagen_tag = mutagen_modules[self.file_type](self.filename)

        for item in data.keys():
            try:
                frame = self.frames[item]
                mutagen_tag[frame] = unicode(data[item])
                if not new_tag:
                    mutagen_tag.save()
                else: 
                    mutagen_tag.save(self.filename)
            except KeyError:
                failed.append(item)
        return failed
                
        



