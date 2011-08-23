#!/usr/bin/python

import os
import sys
import shutil
import time
import string
import pprint
import sqlalchemy as sqla
import sqlalchemy.orm as sqla_orm
import sqlalchemy.orm.exc as sqla_orm_exc
import sqlalchemy.ext.declarative as sqla_dec
import sqlalchemy.sql as sqla_sql
import sqlalchemy.ext.associationproxy as sqla_assoc

import tagtools
import jallen.dirsearch as dirsearch
import jallen.dictools as dictools
import jallen.ltools as ltools
import jallen.dirtools as dirtools

#Constants
REQ_SONG_DATA = ["TITLE", "ALBUM", "ARTIST"]
SUPPORTED_TYPES = [".mp3", ".m4a", ".ogg",".oga",".flac"]

#SQL Alchemy Pre-setup
sqla_engine = None
SqlaSession = sqla_orm.sessionmaker()
SqlaBase = sqla_dec.declarative_base()

#Associate tags with songs
song_tag_table = sqla.Table('song_tag', SqlaBase.metadata,
    sqla.Column('song_id', sqla.Integer, sqla.ForeignKey('song.id')),
    sqla.Column('tag_id', sqla.Integer, sqla.ForeignKey('tag.id')),
)

class Library(SqlaBase):
    __tablename__ = 'library'
    id = sqla.Column(sqla.Integer, primary_key=True)
    location = sqla.Column(sqla.String)
    type = sqla.Column(sqla.Enum('main','local','remote'))
    song_files = sqla_orm.relationship("SongFile",backref='library')

    def __init__(self, location, type):
        self.location = location
        self.type = type
        
    def __repr__(self):
        songs_list = [(song_item.song.id, song_item.location) for song_item \
                        in self.song_files]
        return "<Library('{0}','{1}','{2}'>".\
                format(self.location, self.type, songs_list)

class Song(SqlaBase):
    __tablename__ = 'song'
    id = sqla.Column(sqla.Integer, primary_key=True)
    title = sqla.Column(sqla.String)
    artist = sqla.Column(sqla.String, default="Unknown Artist")
    album = sqla.Column(sqla.String, default="Unknown Album")
    tags = sqla_orm.relationship("Tag", secondary=song_tag_table,
                                    backref="songs",lazy="dynamic")
    
    def __init__(self, title, artist="", album=""):
        self.title = title
        self.artist = artist or self.artist
        self.album = album or self.album

    def __repr__(self):
        tags_list = [(tag_item.frame,tag_item.value) for tag_item in self.tags]
        return "<Song('{0}','{1}','{2}','{3}','{4}')>".\
                    format(self.id, self.title,self.artist, self.album, tags_list)

class SongFile(SqlaBase):
    __tablename__ = 'songfile'
    library_id = sqla.Column(sqla.Integer, sqla.ForeignKey('library.id'),
                primary_key=True)
    song_id = sqla.Column(sqla.Integer, sqla.ForeignKey('song.id'),
                primary_key=True)
    location = sqla.Column(sqla.String)
    song = sqla_orm.relationship(Song, backref="song_files")

    def __init__(self, song,location):
        self.song = song
        self.location = location

    def __repr__(self):
        return "<SongFile({0})>".format(self.location)

class Tag(SqlaBase):
    __tablename__ = 'tag'
    id = sqla.Column(sqla.Integer, primary_key=True)
    frame = sqla.Column(sqla.String)
    value = sqla.Column(sqla.String)

    def __init__(self, frame, value):
        self.frame = frame
        self.value = value

    def __repr__(self):
        return "<Tag('{0}'='{1}')>".format(self.frame, self.value)

playlist_song_table = sqla.Table('playlist_song', SqlaBase.metadata,
    sqla.Column('playlist_id', sqla.Integer, sqla.ForeignKey('playlist.id')),
    sqla.Column('song_id', sqla.Integer, sqla.ForeignKey('song.id'))
)

class Playlist(SqlaBase):
    __tablename__ = 'playlist'
    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String)
    songs = sqla_orm.relationship(Song)
    songs = sqla_orm.relationship("Song",
                    secondary=playlist_song_table,
                    backref="playlists")

    def __init__(self,name):
        self.name = name

    def __repr__(self):
        song_ids = [song.title for song in self.songs]
        return "<Playlist('{0}','{1}')>".format(self.name,song_ids)

#Setup global access to database
def initialize_sql(db_directory):
    global sqla_engine
    sqla_engine = sqla.create_engine('sqlite:///:memory:')
    global SqlaSession
    SqlaSession.configure(bind=sqla_engine)
    global SqlaBase
    SqlaBase.metadata.bind = sqla_engine
    SqlaBase.metadata.create_all()

def get_session():
    global SqlaSession
    return SqlaSession()

def close_session(session):
    session.commit()
    session.close()

#Debugging
def dump():
    sqla_session = get_session()
    print "\n\n--Libraries--\n"
    pprint.pprint(sqla_session.query(Library).join("song_files").all())
    print "\n\n--Playlists--\n"
    pprint.pprint(sqla_session.query(Playlist).all())
    print "\n\n--Songs--\n"
    pprint.pprint(sqla_session.query(Song).all())
    print "\n\n--Tags--\n"
    pprint.pprint(sqla_session.query(Tag).all())
    print "\n\n--SongFiles--\n"
    pprint.pprint(sqla_session.query(SongFile).all())
    close_session(sqla_session)

def get_libraries():
    sqla_session = get_session()
    libraries_list = sqla_session.query(Library.id).all()
    close_session(sqla_session)
    return libraries_list

#Handle SQL Alchemy interface
class ManageLibrary():
    def __init__(self, user_id):
        self.user_id = user_id

    def load(self, library_id):
        self.library_id = library_id
        
    def create(self, location, type):
        sqla_session = get_session()
        library = Library(location,type)
        sqla_session.add(library)
        sqla_session.commit()
        library_id = library.id
        close_session(sqla_session)

    def delete(self):
        sqla_session = get_session()
        library = sqla_session.query(Library).get(self.library_id)
        sqla_session.delete(library)
        close_session(sqla_session)

    def get_songs(self):
        sqla_session = get_session()
        library = sqla_session.query(Library).get(self.library_id)
        song_list = [song_file.song.id for song_file in library.song_files]
        close_session(sqla_session)
        return song_list

    def add(self, location,song_id=0):
        if not song_id:
            song_id = add_song(location)
        sqla_session = get_session()
        library = sqla_session.query(Library).get(self.library_id)
        song = sqla_session.query(Song).get(song_id)
        if song.id not in self.get_songs():
            library.song_files.append(SongFile(song,location))
            sqla_session.commit()
        close_session(sqla_session)

    def remove(self, song_id):
        sqla_session = get_session()
        library = sqla_session.query(Library).get(self.library_id)
        song = sqla_session.query(Song).get(song_id)
        song.libraries.remove(library)
        close_session(sqla_session)

def change_tag(song_id, frame, value, write_tag=False):
    frame = frame.upper()
    remove_tags(song_id,frame)
    sqla_session = get_session()
    song = sqla_session.query(Song).get(song_id)
    if frame in REQ_SONG_DATA:
        exec('song.'+frame.lower()+'=\''+value+'\'')
    else:
        try:
            tag = sqla_session.query(Tag).filter(tag.frame==frame)\
                        .filter(tag.value==value).one()
        except:
            tag = Tag(frame,value)
            sqla_session.add(tag)
        song.tags.append(tag)
    if write_tag:
        locations = [song_file.location for song_file in song.song_files]
        for location in locations:
            song_tag = tagtools.tag_handler(location)
            song_tag.write({frame:value})
    close_session(sqla_session)

def remove_tags(song_id,frame):
    frame = frame.upper()
    sqla_session = get_session()
    song = sqla_session.query(Song).get(song_id)
    existing_tags = song.tags.filter(Tag.frame==frame).all()
    if existing_tags:
        for existing_tag in existing_tags:
            existing_tag.songs.remove(song)
            if not existing_tag.songs:
                sqla_session.delete(existing_tag)
    close_session(sqla_session)
                
def load_tag(song_id,location):
    sqla_session = get_session()
    song = sqla_session.query(Song).get(song_id)
    song_tag = tagtools.tag_handler(location)
    song_data,failed = song_tag.read(ignore=REQ_SONG_DATA+["SONGID"])
    for frame in song_data.keys():
        if song_data[frame] not in song.tags.\
                    filter(Tag.frame==frame).all():
            change_tag(song_id,frame,song_data[frame],write_tag=False)
    close_session(sqla_session)

def get_song_data(song_id):
    sqla_session = get_session()
    song = sqla_session.query(Song).get(song_id)
    song_data = {}
    song_data['TITLE'] = song.title
    song_data['ARTIST'] = song.artist
    song_data['ALBUM'] = song.album
    song_data['LOCATIONS'] = [song_file.location for song_file in song.song_files]
    for tag in song.tags:
        song_data[tag.frame] = tag.value
    close_session(sqla_session)
    return song_data

def add_song(location):
    sqla_session = get_session()
    song_tag = tagtools.tag_handler(location)
    song_data,failed = song_tag.read(REQ_SONG_DATA,force=True)
    song = Song(song_data['TITLE'],song_data['ARTIST'],song_data['ALBUM'])
    sqla_session.add(song)
    sqla_session.commit()
    song_id = song.id
    close_session(sqla_session)
    load_tag(song_id,location)
    return song_id

def get_playlists():
    sqla_session = get_session()
    playlist = sqla_session.query(Playlist).get(playlist_id)
    playlist.songs.append(sqla_session.query(Song).get(song_id))
    close_session(sqla_session)
class ManagePlaylist():
    def load(self,playlist_id):
        self.playlist_id = playlist_id
    def create(self,name):
        sqla_session = get_session()
        playlist = Playlist(name)
        sqla_session.add(playlist)
        sqla_session.commit()
        self.playlist_id = playlist.id
        close_session(sqla_session)

    def add(self,song_id):
        sqla_session = get_session()
        playlist = sqla_session.query(Playlist).get(self.playlist_id)
        playlist.songs.append(sqla_session.query(Song).get(song_id))
        close_session(sqla_session)

    def remove(self,song_id):
        sqla_session = get_session()
        playlist = sqla_session.query(Playlist).get(self.playlist_id)
        playlist.songs.remove(sqla_session.query(Song).get(song_id))
        close_session(sqla_session)

#"""
#Tools to manage library directory
#"""

#def update_library():
#    hd_tracks = scan_directory()
#    for hd_track_id in hd_tracks.keys():
#        try:
#            self.tracks[hd_track_id]
#            for data_item in self.hd_tracks[hd_track_id]:
#                self.tracks[hd_track_id][data_item] = self.hd_tracks[hd_track_id][data_item]
#        except KeyError:
#
#    for track_id in ltools.subtract(self.tracks.keys(), self.hd_tracks.keys()):
#        del self.tracks[track_id]
#    self.write()
#
#
#def import_track(self, track, keep_orig=True):
#    """
#    Keyword arguments:
#    track (string) -- file location
#    """
#    track_id = self.get_new_id()
#    media = add_file(self.library_info['location'], track, track_id, self.library_info['libraryid'], keep_orig)
#    track_data = dictools.make_keys_lower(tagtools.get_metadata(track, self.req_track_info, self.library_info['libraryid']))
#    track_data['location'] = track
#    self.tracks[track_id] = track_data
#    self.write()
#    return track_id
#

#
#def scan_directory(directory,user_id):
#        hd_files = dirsearch.search(directory, supported_types)
#        hd_tracks = {}
#        for hd_file in hd_files:
#            full_p = os.path.join(directory, hd_file)
#            hd_file_tag = tagtools.make_tag_object(full_p,user_id)
#            hd_file_data = hd_file_tag.read(req_track_info)
#            hd_file_data['location'] = full_p
#            try:
#                hd_file_id = int(hd_file_data['USERID'])
#                del hd_file_data['USERID']
#            except KeyError:
#                hd_file_id = 0
#            hd_file_data = dictools.make_keys_lower(hd_file_data)
#            hd_tracks[hd_file_id] = hd_file_data
#        return hd_tracks
#
#def add_file(directory, track, track_id, library_id, keep_orig=True):
#    """
#    Keyword arguments:
#    directory (string) -- library directory
#    track (string) -- file location
#    track_id (int) -- track ID
#    keep_orig (boolean) -- deletes original file on copy if False
#    """
#    track = fix_path(directory, track, keep_orig)
#    tagtools.write_metadata(track, {'LIBRARYID': str(track_id)}, library_id)
#    return track
#
#def run_cleanup(directory, library_id, keep_orig=False):
#    """Keyword arguments:
#    directory (string) -- library directory
#    """
#    changed_files = []
#    file_list = dirsearch.search(directory, [".mp3", ".m4a"])
#
#    for item in file_list:
#        fullp = os.path.join(directory, item)
#        newp = fix_path(directory, fullp, keep_orig)
#        if newp != fullp:
#            try:
#                track_id = tagtools.get_metadata(newp, ("LIBRARYID",), library_id)["LIBRARYID"]
#                changed_files.append((track_id, newp))
#            except KeyError: pass
#    dirtools.cleanup(directory, [".DS_Store"])
#    return changed_files
#
#def fix_path(directory, fpath, keep_orig=False):
#    metadata = tagtools.get_metadata(fpath, ('TITLE','ARTIST', 'ALBUM'))
#    try: metadata['TITLE']
#    except KeyError: return fpath
#    try: metadata['ARTIST']
#    except KeyError: metadata['ARTIST'] = "Unknown Artist"
#    try: metadata['ALBUM']
#    except KeyError: metadata['ALBUM'] = "Unknown Album"
#    ext = fpath.split('.')[-1]
#    correct_path = os.path.join(directory, metadata['ARTIST'], metadata['ALBUM'], metadata['TITLE']) + '.' + ext
#    correct_path = correct_path.replace(":", "_")
#    if fpath != correct_path:
#        if not keep_orig: os.renames(fpath, correct_path)
#        else:
#            parent_dir = os.path.split(correct_path)[0]
#            if not os.path.exists(parent_dir):
#                os.makedirs(parent_dir)
#            if os.path.exists(correct_path):
#                os.remove(correct_path)
#            shutil.copy2(fpath, correct_path)
#    return correct_path
#
#if __name__ == '__main__':
#    if len(sys.argv) > 1:
#        args = sys.argv
#        library_file = args[1]
#        new_library = Library(library_file)
#        #new_library.create_xml()
#        new_library.load()
#        for x in range(2, len(sys.argv)):
#            new_library.add_track(args[x])
#        new_library.update_library()
#        print "done"
#
#    else:
#        print """
#Usage: Formats xml file with proper newlines and tabs
#Syntax: python formatxml.py [xml file]
#"""
