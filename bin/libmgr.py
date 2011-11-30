"""Music library manager for Mist program. Uses SQL Alchemy for persistant storage."""

__author__ = "Jonathan Allen"
__all__ = ["SqlaSession", "DatabaseError", "NonexistantEntryError",
           "ConflictingEntriesError", "DirectoryError", "Repository", "Song",
           "SongFile", "Tag", "Playlist", "signalEmitter"]

import os
import re
import shutil
import types
import thread
import Queue

from PySide import QtCore

from metaedit import *
from jonathan import dirtools
from jonathan.dictools import *


#===============================================================================
# Constants
#===============================================================================
REQ_SONG_DATA = ["TITLE", "ALBUM", "ARTIST"]
SUPPORTED_FILE_TYPES = [".mp3", ".m4a", ".ogg", ".oga", ".flac"]
SUPPORTED_MIMETYPES = ["audio/mpeg", "audio/flac", "audio/mp4", "audio/ogg"]


#===============================================================================
# SQL Alchemy Pre-setup
#===============================================================================
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, session
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, Unicode

_sqlaEngine = None
SqlaSession = scoped_session(sessionmaker())
_guiSession = None
_SqlaBase = declarative_base()
_workerRunning = True
_workerSession = None
_workerThread = None
workerQueue = Queue.Queue()

#===============================================================================
# Exceptions
#===============================================================================
class DatabaseError(Exception):
    pass

class NonexistantEntryError(DatabaseError):
    pass

class ConflictingEntriesError(DatabaseError):
    pass

class DirectoryError(Exception):
    pass

#===============================================================================
# Thread related function decorators
#===============================================================================
def attachSession(function):
    def wrapper(self, *args, **kwargs):
        self.sqlaSession = SqlaSession()
        try:
            if self not in self.sqlaSession: self.sqlaSession.add(self)
            return function(self, *args, **kwargs)
        except InvalidRequestError: pass
    return wrapper

def initialize(function):
    def wrapper(self, *args, **kwargs):
        if not getattr(self, 'initialized', None): self.setup()
        return function(self, *args, **kwargs)
    return wrapper


#===============================================================================
# SQL Alchemy Types
#===============================================================================
class UnicodeString(TypeDecorator):
    """Safely coerce Python bytestrings to Unicode
    before passing off to the database."""

    impl = Unicode

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            value = value.decode('utf-8')
        return value


#===============================================================================
# SQL Alchemy Tables
#===============================================================================
"""
Secondary table to associate tags with songs. Relationship is bidirectional and many-to-many.
"""
songTagTable = sqlalchemy.Table('songTag', _SqlaBase.metadata,
    sqlalchemy.Column('songId', sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id')),
    sqlalchemy.Column('tagId', sqlalchemy.Integer, sqlalchemy.ForeignKey('tag.id')),
)

"""
Secondary table to associate songs with playlists. Relationship is unidirectional and many-to-many.
"""
playlistSongTable = sqlalchemy.Table('playlistSong', _SqlaBase.metadata,
    sqlalchemy.Column('playlistId', sqlalchemy.Integer, sqlalchemy.ForeignKey('playlist.id')),
    sqlalchemy.Column('songId', sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'))
)


class Repository(_SqlaBase):
    """
    Table to store information about repositories. Stores repository name, repository
    directory, repository settings, and pending repository transfers. 
    """
    __tablename__ = 'repository'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    name = sqlalchemy.Column(UnicodeString)
    location = sqlalchemy.Column(UnicodeString)
    monitored = sqlalchemy.Column(sqlalchemy.Boolean)
    managed = sqlalchemy.Column(sqlalchemy.Boolean)
    directoryStructure = sqlalchemy.Column(UnicodeString)
    pendingTransfers = sqlalchemy.Column(sqlalchemy.PickleType(mutable = True))
    songFiles = relationship("SongFile", backref = 'repository')

    DEFAULT_DIRECTORY_STRUCTURE = "%ARTIST%/%ALBUM%/%TITLE%"

    def __init__(self, name, location, \
                 directoryStructure = DEFAULT_DIRECTORY_STRUCTURE, \
                 monitored = True, managed = True):
        self.name = name
        self.location = location
        self.monitored = monitored
        self.managed = managed
        self.directoryStructure = directoryStructure
        self.pendingTransfers = {}

    @attachSession
    @initialize
    def __contains__(self, item):
        if isinstance(item, types.IntType):
            return any([item == song.id for song in self.getSongs()])
        if isinstance(item, Song):
            return item in self.getSongs()
        raise TypeError("{} is not of type Song or Song.id".format(item))

    @attachSession
    def __repr__(self):
        songsList = [songItem.songId for songItem in self.songFiles]
        return "<Repository({}, {}, {}, {}, {}, {})>". \
                format(self.name, self.location, self.directoryStructure,
                       self.managed, self.monitored, songsList)

    @attachSession
    def __str__(self):
        songsList = [songItem.songId for songItem in self.songFiles]
        output = "Repository:"
        output += "\n\tName: {}".format(self.name)
        output += "\n\tLocation: {}".format(self.location)
        output += "\n\tDirectoryStructure: {}".format(self.directoryStructure)
        output += "\n\tManaged: {}".format(self.managed)
        output += "\n\tMonitored: {}".format(self.monitored)
        output += "\n\tSongs: {}".format(songsList)
        return output

    @attachSession
    def delete(self):
        repositoryName = self.name
        [self.sqlaSession.delete(songFile) for songFile in self.songFiles]
        self.sqlaSession.delete(self)
        self.sqlaSession.commit()
        signalEmitter.repositoryRemoved.emit(repositoryName)

    @attachSession
    def setup(self):
        self.initialized = True
        try:
            self.directory = ManageDirectory(self)
        except DirectoryError:
            signalEmitter.repositoryDisabled.emit(self.id)
            self.directory = None
        if self.directory:
            for songId, (action, arguments) in self.pendingTransfers.items():
                song = self.sqlaSession.query(Song).get(songId)
                if action == "add":
                    self.addSongs({arguments[0], song}, arguments[1])
                elif action == "remove":
                    self.removeSongs([song])
                del self.pendingTransfers[songId]

    @attachSession
    @initialize
    def update(self):
        if not self.directory or not self.monitored: return
        [self.sqlaSession.delete(songFile) for songFile in self.songFiles
                    if not os.path.exists(songFile.location)]
        self.sqlaSession.commit()

        directoryFiles = self.directory.songs
        missingSongs = songs = self.getSongs()
        missingSongs.difference_update(directoryFiles)
        [self.removeSongs([song], False) for song in missingSongs]

        newSongs = directoryFiles - songs

        signalEmitter.longTask.emit("Updating Repository: " + self.name, len(newSongs))
        self.addSongs(newSongs, keepFiles = not self.managed)
        signalEmitter.longTaskDone.emit()

        self.directory.fixAllPaths()

    @attachSession
    @initialize
    def setName(self, value):
        if self.name == value: return
        if self.sqlaSession.query(Repository).filter(Repository.name == value).all():
            raise DatabaseError("Repository", {"name":value}, DatabaseError.Conflicting)
        signalEmitter.repositoryRemoved.emit(self.name)
        self.name = value
        self.sqlaSession.commit()
        signalEmitter.repositoryAdded.emit(self.id)

    @attachSession
    @initialize
    def setLocation(self, value):
        if self.location == value: return
        if self.sqlaSession.query(Repository).filter(Repository.location == value).all():
            raise DatabaseError("Repository", {"location":value}, DatabaseError.Conflicting)
        self.location = value
        self.sqlaSession.commit()
        self.setup()
        self.update()

    @attachSession
    @initialize
    def setManaged(self, value):
        if self.managed == value: return
        self.managed = value
        self.sqlaSession.commit()
        self.update()

    @attachSession
    @initialize
    def setMonitored(self, value):
        if self.monitored == value: return
        self.monitored = value
        self.sqlaSession.commit()
        self.update()

    @attachSession
    @initialize
    def getSongs(self):
        return set([songFile.song for songFile in self.songFiles])

    @attachSession
    @initialize
    def addSongs(self, songs, keepFiles = False):
        songs = songs - self.getSongs()

        for (song, location) in songs.items():
            if not self.directory:
                self.pendingTransfers[song.id] = ("add", [location, keepFiles])
            else:
                if self.managed:
                    location = self.directory.fixFilePath(location, song, keepFiles)
                self.songFiles.append(SongFile(song, location))
        self.sqlaSession.commit()
        signalEmitter.repositoryChanged.emit(self.id)

    @attachSession
    @initialize
    def removeSongs(self, songs, keepFiles = False):
        self.pendingTransfers = self.pendingTransfers - songs

        songs = set(songs).intersection(self.getSongs())

        if not self.directory:
            for song in songs:
                if song in self:
                    self.pendingTransfers[song.id] = ("remove", [])

        else:
            songFiles = [songFile for songFile in self.songFiles if songFile.song in songs]
            for songFile in songFiles:
                if not keepFiles or self.monitored:
                    if os.path.exists(songFile.location):
                        os.remove(songFile.location)
                self.sqlaSession.delete(songFile)
        self.sqlaSession.commit()
        signalEmitter.repositoryChanged.emit(self.id)


class Song(_SqlaBase):
    __tablename__ = 'song'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    title = sqlalchemy.Column(UnicodeString)
    tags = relationship("Tag", secondary = songTagTable,
                                    backref = "songs", lazy = "dynamic")

    DEFAULT_METADATA = {
                        "ARTIST": "Unknown",
                        "ALBUM": "Unknown"
    }

    def __init__(self, title):
        self.title = title

    @attachSession
    def __contains__(self, item):
        if isinstance(item, types.IntType):
            return any([item == tag.id for tag in self.tags])
        if isinstance(item, Tag):
            return item in self.tags.all()
        raise TypeError("{} is not of type Tag or Tag.id".format(item))

    @attachSession
    def __repr__(self):
        locations = [songFile.location for songFile in self.songFiles]
        return "<Song({}, {}, {})>".\
                    format(self.id, self.title, locations)

    @attachSession
    def __str__(self):
        metadata = self.getMetadata()
        metadata.keysUpper()
        locations = [songFile.location for songFile in self.songFiles]
        output = "Song:"
        output += "\n\tId: {}".format(self.id)
        output += "\n\tName: {}".format(self.title)
        output += "\n\tArtist: {}".format(metadata["ARTIST"])
        output += "\n\tAlbum: {}".format(metadata["ALBUM"])
        output += "\n\tLocations: {}".format(locations)
        del metadata["ARTIST"]
        del metadata["ALBUM"]
        del metadata["TITLE"]
        output += "\n\tTags: {}".format(metadata)
        return output

    @attachSession
    def partialUpdate(self, location):
        """Augments current data with metadata from location"""

        songMetadataHandler = Metadata(location)
        songMetadata = songMetadataHandler.read() + Song.DEFAULT_METADATA
        self.addTags([getTag(tagName, tagValue) for (tagName, tagValue)
                      in songMetadata.items()], write = True)

    @attachSession
    def update(self, location):
        """Resets all data to metadata from location"""

        songMetadataHandler = Metadata(location)
        songMetadata = songMetadataHandler.read()
        if "TITLE" not in songMetadata:
            self.title = getUnknownTitle()
        else:
            self.title = songMetadata["TITLE"]
            del songMetadata["TITLE"]
        self.sqlaSession.commit()
        self.addTags([getTag(tagName, tagValue) for (tagName, tagValue)
                      in songMetadata.items()], write = True)
        self.checkForDuplicates()

    @attachSession
    def delete(self):
        self.sqlaSession.query(SongFile).filter(SongFile.song == self).delete()

        playlists = self.sqlaSession.query(Playlist) \
                                .join(Playlist.songs).filter(Song.id == self.id)
        [playlist.removeSong(self) for playlist in playlists]
        self.sqlaSession.commit()
        self.removeTags(self.tags, write = False)

        songId = self.id
        self.sqlaSession.delete(self)
        self.sqlaSession.commit()
        signalEmitter.songsRemoved.emit([songId])

    @attachSession
    def getSongFiles(self):
        return set(self.sqlaSession.query(SongFile).filter(SongFile.song == self).all())

    @attachSession
    def setTitle(self, value):
        self.title = value
        self.sqlaSession.commit()
        signalEmitter.songsChanged.emit([self.id])

    @attachSession
    def getMetadata(self):
        return StringDictionary(Song.DEFAULT_METADATA.items()
                    + [(tag.name, tag.value) for tag in self.tags]
                    + [("TITLE", self.title)])

    @attachSession
    def addTags(self, tags, write = False):
        tags = [tag for tag in tags if tag not in self]
        for newTag in tags:
            self.removeTags([tag for tag in self.tags
                             if tag.name == newTag.name], write = False)
            self.tags.append(newTag)
        if write:
            data = ExtendedDictionary([(newTag.name, newTag.value) for newTag in tags])
            locations = self.getLocations()
            for location in locations.values():
                try:
                    Metadata(location).write(data)
                except:
                    pass
        self.sqlaSession.commit()
        self.checkForDuplicates()
        signalEmitter.songsChanged.emit([self.id])


    @attachSession
    def removeTags(self, tags, write = False):
        tags = [tag for tag in tags if tag in self]
        [self.tags.remove(tag) for tag in tags]
        self.sqlaSession.commit()
        if write:
            for location in self.getLocations().values():
                fileMetadata = Metadata(location)
                [fileMetadata.removeTag(tag.name) for tag in tags]

        signalEmitter.songsChanged.emit([self.id])

    @attachSession
    def modifyLocation(self, new):
        [setattr(songFile, "location", new) for songFile in self.getSongFiles()]
        self.sqlaSession.commit()
        signalEmitter.songsChanged.emit([self.id])

    @attachSession
    def getLocation(self, repository = None):
        locations = self.getLocations()
        if repository:
            if repository in locations:
                return locations[repository]
        else:
            activeRepositories = [repository for repository
                                  in locations.keys() if repository.directory]
            if activeRepositories:
                return locations[activeRepositories[0]]
        return None

    @attachSession
    def getLocations(self):
        return ExtendedDictionary((self.sqlaSession.query(Repository) \
                     .get(songFile.repositoryId), songFile.location) \
                    for songFile in self.songFiles)

    @attachSession
    def writeMetadata(self):
        for location in self.getLocations().values():
            try:
                songMetadataHandler = Metadata(location)
                songMetadataHandler.write(self.getMetadata())
            except NonexistantFileError:
                self.songFiles.filter(SongFile.location == location).delete()
            except UnsupportedFiletypeError:
                pass

    def merge(self, others):
        songFiles = [songFiles for songFiles
                     in reduce(lambda x, y: x + y.getLocations.items(), others, [])]
        [repository.addSong(location, self) for (repository, location) in songFiles]
        playlists = set([])
        for song in others:
            [playlists.add(playlist) for playlist
                        in self.sqlaSession.query(Playlist)
                                    .filter(Playlist.songs.contains(song))]
        [playlist.addSong(song) for playlist in playlists]
        [other.delete() for other in others]

    def checkForDuplicates(self):
        metadata = self.getMetadata()
        duplicates = self.sqlaSession.query(Song) \
                    .filter(Song.title == self.title).filter(Song.id != self.id) \
                    .filter(Song.tags.contains(getTag("ARTIST", metadata["ARTIST"]))) \
                    .filter(Song.tags.contains(getTag("ALBUM", metadata["ALBUM"]))).all()
        self.merge(duplicates)


class SongFile(_SqlaBase):
    __tablename__ = 'songfile'
    repositoryId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('repository.id'),
                primary_key = True)
    songId = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('song.id'),
                primary_key = True)
    location = sqlalchemy.Column(UnicodeString)
    song = relationship(Song, backref = "songFiles")

    def __init__(self, song, location):
        self.song = song
        self.songId = song.id
        self.location = location

    @attachSession
    def __repr__(self):
        repository = self.sqlaSession.query(Repository).get(self.repositoryId)
        return "<SongFile({}, {})>".format(repository.name, self.location)

    @attachSession
    def __str__(self):
        repository = self.sqlaSession.query(Repository).get(self.repositoryId)
        output = "SongFile:"
        output += "\n\tRepository: {}".format(repository.name)
        output += "\n\tLocation: {}".format(self.location)
        output += "\n\tSong Id: {}".format(self.songId)
        return output


class Tag(_SqlaBase):
    __tablename__ = 'tag'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    name = sqlalchemy.Column(UnicodeString)
    value = sqlalchemy.Column(UnicodeString)

    def __init__(self, name, value):
        name = name.upper()
        if name == "TITLE": raise ValueError("Cannot make TITLE tag.")
        self.name = name
        self.value = value

    @attachSession
    def __repr__(self):
        return "<Tag({}: {})>".format(self.name, self.value)

    @attachSession
    def __str__(self):
        songsList = [song.id for song in self.songs]
        output = "Tag:"
        output += "\n\tName: {}".format(self.name.capitalize())
        output += "\n\tValue: {}".format(self.value)
        output += "\n\tSongs: {}".format(songsList)
        return output
    @attachSession
    def delete(self):
        tagId = self.id
        [song.removeTags([self]) for song in self.songs]

        self.sqlaSession.delete(self)
        self.sqlaSession.commit()
        signalEmitter.tagsRemoved.emit([tagId])

    @attachSession
    def setValue(self, value):
        if self.value == value: return
        existingTag = self.sqlaSession.query(Tag).filter(Tag.name == self.name) \
            .filter(Tag.value == value).first()
        if existingTag:
            existingTag.merge(self)
        else:
            self.value = value
            signalEmitter.tagsChanged.emit([self.id])

    def merge(self, other):
        for song in other.songs:
            song.addTags([self], write = True)
        other.delete()


class Playlist(_SqlaBase):
    __tablename__ = 'playlist'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key = True)
    name = sqlalchemy.Column(UnicodeString)
    songs = relationship("Song",
                    secondary = playlistSongTable,
                    backref = "playlists")

    def __init__(self, name):
        self.name = name

    @attachSession
    def __contains__(self, item):
        if isinstance(item, types.IntType):
            return any([item == song.id for song in self.songs])
        if isinstance(item, Song):
            return item in self.songs
        raise TypeError("{} is not of type Song or Song.id".format(item))

    @attachSession
    def __repr__(self):
        songsList = [song.id for song in self.songs]
        return "<Playlist({}, {})>".format(self.name, songsList)

    @attachSession
    def __str__(self):
        songsList = [song.id for song in self.songs]
        output = "Playlist:"
        output += "\n\tName: {}".format(self.name)
        output += "\n\tSongs: {}".format(songsList)
        return output

    @attachSession
    def delete(self):
        name = self.name
        self.sqlaSession.delete(self)
        self.sqlaSession.commit()
        signalEmitter.playlistRemoved.emit(name)

    @attachSession
    def setName(self, value):
        if self.name == value: return
        if self.sqlaSession.query(Playlist).filter(Playlist.name == value).all():
            raise DatabaseError("Playlist", {"name":value}, DatabaseError.Conflicting)
        signalEmitter.playlistRemoved.emit(self.name)
        self.name = value
        self.sqlaSession.commit()
        signalEmitter.playlistAdded.emit(self.id)

    @attachSession
    def addSongs(self, songs):
        songs = set(songs)
        songs.difference_update(self.songs)
        [self.songs.append(song) for song in songs]
        self.sqlaSession.commit()
        signalEmitter.playlistChanged.emit(self.id)

    @attachSession
    def removeSongs(self, songs):
        songs = set(songs).intersection(self.songs)
        [self.songs.remove(song) for song in songs]
        self.sqlaSession.commit()
        signalEmitter.playlistChanged.emit(self.id)



#===============================================================================
# Setup engine and initialize session
#===============================================================================
def setupSqlAlchemy(dbDirectory):
    if not _sqlaEngine: _setupSqlEngine(dbDirectory)
    _SqlaBase.metadata.create_all()

def resetSql():
    _SqlaBase.metadata.drop_all()
    setupSqlAlchemy("")

def _setupSqlEngine(dbFile):
    global _sqlaEngine
    global _guiSession
    global _SqlaBase
    global _workerThread

    _sqlaEngine = sqlalchemy.create_engine("sqlite:///{}".format(dbFile))
    SqlaSession.configure(bind = _sqlaEngine)
    session.Session.close_all()
    _sqlaMasterSession = SqlaSession()
    _SqlaBase.metadata.bind = _sqlaEngine

    _workerThread = thread.start_new_thread(_runBackgroundThread, ())

#===============================================================================
# PySide Signals
#===============================================================================
class SignalEmitter(QtCore.QObject):
    repositoryAdded = QtCore.Signal(int)
    repositoryChanged = QtCore.Signal(int)
    repositoryRemoved = QtCore.Signal(str)
    repositoryDisabled = QtCore.Signal(int)

    playlistAdded = QtCore.Signal(int)
    playlistChanged = QtCore.Signal(int)
    playlistRemoved = QtCore.Signal(str)

    songsAdded = QtCore.Signal(list)
    songsRemoved = QtCore.Signal(list)
    songsChanged = QtCore.Signal(list)

    tagsAdded = QtCore.Signal(list)
    tagsRemoved = QtCore.Signal(list)
    tagsChanged = QtCore.Signal(list)

    longTask = QtCore.Signal(str, int)
    longTaskIncrement = QtCore.Signal(int)
    longTaskDone = QtCore.Signal()


    def __init__(self, parent = None):
        QtCore.QObject.__init__(self, parent)

signalEmitter = SignalEmitter()


#===============================================================================
# Debugging Tools
#===============================================================================
def dump(fileName):
    sqlaSession = SqlaSession()
    output = "Repositories:\n"
    for item in sqlaSession.query(Repository).all():
        output += "\n" + item.__str__()
    output += "\n\n" + "="*80 + "\n\nPlaylists:\n"
    for item in sqlaSession.query(Playlist).all():
        output += "\n" + item.__str__()
    output += "\n\n" + "="*80 + "\n\nSongs:\n"
    for item in sqlaSession.query(Song).all():
        output += "\n" + item.__str__()
    output += "\n\n" + "="*80 + "\n\nTags:\n"
    for item in sqlaSession.query(Tag).all():
        output += "\n" + item.__str__()
    output += "\n\n" + "="*80 + "\n\nSongFiles:\n"
    for item in sqlaSession.query(SongFile).all():
        output += "\n" + item.__str__()
    open(fileName, 'w').write(output)

def _runBackgroundThread():
    global _backgroundSession
    _backgroundSession = SqlaSession()
    while _workerRunning:
        task, args = workerQueue.get()
        task(*args)
        workerQueue.task_done()
    thread.exit()


#===============================================================================
# Repository Functions
#===============================================================================
def createRepository(name, location, \
                     directoryStructure = Repository.DEFAULT_DIRECTORY_STRUCTURE, \
                     monitored = True, managed = True):
    sqlaSession = SqlaSession()
    if sqlaSession.query(Repository).filter(Repository.name == name).all():
        raise DatabaseError("Repository", {"name": name}, DatabaseError.Conflicting)
    if sqlaSession.query(Repository).filter(Repository.location == location).all():
            raise DatabaseError("Repository", {"location":location}, DatabaseError.Conflicting)
    repository = Repository(name, location, directoryStructure, monitored, \
                               managed)
    sqlaSession.add(repository)
    sqlaSession.commit()
    workerQueue.put([loadRepository, (repository.id,)])
    return repository

def loadAllRepositories():
    sqlaSession = SqlaSession()
    [workerQueue.put([loadRepository, (repository.id,)]) for repository in sqlaSession.query(Repository.id)]

def loadRepository(id):
    sqlaSession = SqlaSession()
    repository = sqlaSession.query(Repository).get(id)
    repository.update()
    signalEmitter.repositoryAdded.emit(id)


#===============================================================================
# Playlist Functions
#===============================================================================
def createPlaylist(name):
    sqlaSession = SqlaSession()
    if sqlaSession.query(Playlist).filter(Playlist.name == name).all():
        raise DatabaseError("Playlist", {"name": name}, DatabaseError.Conflicting)
    playlist = Playlist(name)
    sqlaSession.add(playlist)
    sqlaSession.commit()
    signalEmitter.playlistAdded.emit(playlist.id)
    return playlist

def loadAllPlaylists():
    sqlaSession = SqlaSession()
    for playlist in sqlaSession.query(Playlist.id):
        signalEmitter.playlistAdded.emit(playlist.id)


#===============================================================================
# Song Functions
#===============================================================================
def loadAllSongs():
    sqlaSession = SqlaSession()
    songs = sqlaSession.query(Song).all()
    signalEmitter.songsAdded.emit([song.id for song in songs])

def createSong(location):
    sqlaSession = SqlaSession()
    if not os.path.exists(location): raise NonexistantFileError("{} does not exist.".format(location))
    songMetadataHandler = Metadata(location)
    metadata = songMetadataHandler.read(REQ_SONG_DATA)
    if "TITLE" not in metadata:
        metadata["TITLE"] = getUnknownTitle()
    song = getSongByMetadata(metadata["TITLE"], metadata.subset(["ARTIST", "ALBUM"]))
    if song: return song
    song = Song(metadata["TITLE"])
    sqlaSession.add(song)
    sqlaSession.commit()
    song.update(location)
    signalEmitter.songsAdded.emit([song.id])
    return song

def getUnknownTitle():
    sqlaSession = SqlaSession()
    unknownSongs = sqlaSession.query(Song).filter(Song.title.like("unknown%")).all()
    counter = 0
    for song in unknownSongs:
        try:
            counter = max(counter, int(song.title.replace("unknown", "")))
        except ValueError: pass
    return "unknown{}".format(counter)

def getSong(id):
    sqlaSession = SqlaSession()
    return sqlaSession.query(Song).get(id)

def getSongByLocation(location):
    sqlaSession = SqlaSession()
    songFile = sqlaSession.query(SongFile).filter(SongFile.location == location) \
                .first()
    if songFile: return songFile.song
    try:
        fileMetadataHandler = Metadata(location)
    except FileError: return None
    metadata = fileMetadataHandler.read(REQ_SONG_DATA)

    song = getSongByMetadata(metadata["TITLE"], metadata.subset(["ARTIST", "ALBUM"]))
    if song: return song
    return createSong(location)

def getSongByMetadata(title, metadata):
    sqlaSession = SqlaSession()
    possibleMatches = sqlaSession.query(Song).filter(Song.title == title)
    for (key, value) in metadata.items():
        possibleMatches = possibleMatches.filter(Song.tags.contains(getTag(key, value)))
    return possibleMatches.first()

#===============================================================================
# Tag Functions
#===============================================================================

def loadAllTags():
    sqlaSession = SqlaSession()
    tags = sqlaSession.query(Tag).all()
    [tag.delete() for tag in tags if not tag.songs]
    signalEmitter.tagsAdded.emit([tag.id for tag in sqlaSession.query(Tag).all()])

def getTag(name, value):
    sqlaSession = SqlaSession()
    name = name.upper()
    tag = sqlaSession.query(Tag).filter(Tag.name == name) \
                .filter(Tag.value == value).first()
    if tag: return tag
    tag = Tag(name, value)
    sqlaSession.add(tag)
    sqlaSession.commit()
    signalEmitter.tagsAdded.emit([tag.id])
    return tag


class ManageDirectory(object):
    """
    Song directory manager
    """
    instances = {}
    def __init__(self, repository):
        self.repository = repository
        self.songs = ExtendedDictionary()
        self.refreshDirectoryStructure()
        self.scanStatus = False

    def __new__(cls, repository):
        if not os.path.isdir(repository.location): raise DirectoryError("{} is not a directory.".format(repository.location))
        if repository in ManageDirectory.instances:
            return ManageDirectory[ManageDirectory.instances]
        self = object.__new__(cls)
        manager = ManageDirectory.instances[repository] = ManageDirectory.__init__(self, repository)
        manager.scan()
        return manager

    def refreshDirectoryStructure(self):
        self.tagNames = re.findall('%[a-zA-Z]+%', self.repository.directoryStructure)
        self.tagNames = [tagName.replace("%", "").upper() for tagName in \
                         self.tagNames]
        self.defaultMetadata = ExtendedDictionary.fromkeys(self.tagNames, "Unknown")

    def scan(self):
        sqlaSession = SqlaSession()
        if not os.path.exists(self.repository.location):
            raise DirectoryError(self.repository.location, DirectoryError.Nonexistant)
        fileNames = dirtools.search(self.repository.location, SUPPORTED_FILE_TYPES, relative = False)

        self.songs = ExtendedDictionary([(songFile.song, songFile.location) for songFile in \
                           sqlaSession.query(SongFile) \
                           .filter(SongFile.repository == self.repository).all() \
                           if songFile.location in fileNames])
        fileNames.difference_update(set(self.songs.values()))
        signalEmitter.longTask.emit("Scanning Directory", len(fileNames))
        for i, fileName in enumerate(fileNames):
            signalEmitter.longTaskIncrement.emit(i)
            try:
                song = getSongByLocation(fileName)
            except FileError:
                continue
            self.songs[song] = fileName
        signalEmitter.longTaskDone.emit()
        self.scanStatus = True

    def formatPath(self, fileName, metadata, number):
        extension = os.path.splitext(fileName)[1]
        output = os.path.join(self.repository.location, self.repository.directoryStructure)

        metadata += self.defaultMetadata
        for tagName, tagValue in metadata.items():
            tagValue = tagValue.replace("/", "_").strip()
            output = output.replace("%{}%".format(tagName), tagValue)
        if number > 0:
            output += "{}".format(number);
        for invalidCharacter in ("\\", ":", "\"", "<", ">", "|", "*", "?"):
            output = output.replace(invalidCharacter, "_")
        output += extension
        return output

    def fixAllPaths(self, keepOriginal = False):
        for i, (song, location) in enumerate(self.songs.items()):
            signalEmitter.longTaskIncrement.emit(i)
            self.fixFilePath(location, song, keepOriginal)
        signalEmitter.longTaskDone.emit()

        dirtools.cleanup(self.repository.location, [".DS_Store"])

    def fixFilePath(self, fileName, song, keepOriginal = False):
        metadata = song.getMetadata()
        correctPath = self.formatPath(fileName, metadata, 0)

        if fileName == correctPath:
            self.songs[song.id] = fileName
            return fileName
        i = 0
        while os.path.exists(correctPath):
                i += 1
                correctPath = self.formatPath(fileName, metadata, i)

        if not keepOriginal:
            os.renames(fileName, correctPath)
            song.modifyLocation(correctPath)

        else:
            parentDirectory = os.path.dirname(correctPath)
            if not os.path.exists(parentDirectory):
                os.makedirs(parentDirectory)
            shutil.copy(fileName, correctPath)
        self.songs[song.id] = correctPath
        return correctPath

    def __contains__(self, other):
        if isinstance(other, Song):
            return any([other.id == song.id for song in self.getSongs])
        else:
            raise TypeError("{} is not of type Song".format(other))

