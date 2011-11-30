import os
import pprint
import unittest

import libmgr
import metaedit
from mistexceptions import *

modulePath = os.path.dirname(os.path.abspath(__file__))
songLibrary = os.path.join(modulePath, "Music Library")
walkmanLibrary = os.path.join(modulePath, "Walkman")

class SimpleLibraryTest(unittest.TestCase):
    def setUp(self):
        libmgr.initializeSql(":memory:")
        self.sqlaSession = libmgr.SqlaSession()
        
class SimpleRepositoryTest(SimpleLibraryTest):
    def setUp(self):
        try:
            SimpleLibraryTest.setUp(self)
            self.repository = libmgr.createRepository("Jonathan Main", \
                                                        songLibrary, managed=True, \
                                                        monitored=True)
            
        except DBConflictError:
            self.repository = self.sqlaSession.query(libmgr.Repository) \
                        .filter(libmgr.Repository.name=="Jonathan Main").one()
                
class ManipulateRepositoryTest(SimpleRepositoryTest):
    def runTest(self):
        
        songFile = os.path.join(modulePath, "sample.mp3")
        metadataHandler = metaedit.metadataHandler(songFile)
        songInfo= metadataHandler.read()
        
        song = self.repository.addSong(songFile, libmgr.createSong(songFile), \
                                       keepOriginal=True)
        assert os.path.exists(songFile)
        assert song in self.repository
        self.repository.removeSong(song)
        assert song not in self.repository
        
class ModifyTagsTest(SimpleRepositoryTest):
    def runTest(self):
        
        song = self.sqlaSession.query(libmgr.Song).all()[0]
        song.addTag(libmgr.getTag('GENRE', 'Rock'), write=True)
        song.addTag(libmgr.getTag('ARTIST', 'Testing'), write=True)
        songInfo = song.getMetadata()
        assert libmgr.getTag("GENRE", "Rock") in song
        assert libmgr.getTag("ARTIST", "Testing") in song
    
class SimplePlaylistTest(SimpleRepositoryTest):
    def setUp(self):
        SimpleRepositoryTest.setUp(self)
        try:
            self.playlist = libmgr.createPlaylist("Favorite Songs")
        except DBConflictError:
            self.playlist = self.sqlaSession.query(libmgr.Playlist) \
                        .filter(libmgr.Playlist.name=="Favorite Songs").one()
    def runTest(self):
        song = self.sqlaSession.query(libmgr.Song).all()[0]
        if song not in self.playlist:
            self.playlist.songs.append(song)
            self.sqlaSession.commit()
        assert self.playlist.name=="Favorite Songs"
        assert song in self.playlist
        libmgr.dump(os.path.join(modulePath, "dump.txt"))


