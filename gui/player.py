__author__ = "jonathan"

from PySide import QtCore
from PySide.phonon import Phonon
import random

import libmgr
from libmgr import *

class Player(QtCore.QObject):
    songPaused = QtCore.Signal()
    songPlaying = QtCore.Signal(Song)
    START_LEWAY_TIME = 3000

    def __init__(self, viewPane, parent):
        QtCore.QObject.__init__(self, parent)
        self.sqlaSession = SqlaSession()

        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.songObject = Phonon.MediaObject(self)
        self.songObject.setTickInterval(1000)
        self.currentSong = None
        self.queuedSources = []
        self.previousSources = []
        self.songList = []
        self.loopPlayback = True
        self.randomPlayback = True
        self.viewPane = viewPane

        self.songObject.stateChanged.connect(self.stateChanged)
        self.songObject.currentSourceChanged.connect(self.sourceChanged)
        self.songObject.aboutToFinish.connect(self.aboutToFinish)

        Phonon.createPath(self.songObject, self.audioOutput)

    @QtCore.Slot(Phonon.State)
    def stateChanged(self, newState):
        if newState == Phonon.PlayingState:
            self.songPlaying.emit(self.currentSong)
        elif newState == Phonon.StoppedState:
            self.songPaused.emit()
        elif newState == Phonon.PausedState:
            self.songPaused.emit()

    @QtCore.Slot(Phonon.MediaSource)
    def sourceChanged(self, source):
        self.songPlaying.emit(self.currentSong)

    @QtCore.Slot(libmgr.Song, list)
    def play(self, song = None, songList = None):
        if songList: self.songList = songList
        if not song:
            if self.currentSong:
                self.songObject.play()
                return
            else:
                song = self.getRandom()
                if not song:
                    return
        self.stop()
        songLocation = song.getLocation()
        if not songLocation:
            self.next()
            return
        self.currentSong = song
        source = Phonon.MediaSource(song.getLocation())
        self.songObject.setCurrentSource(source)
        self.songObject.play()

    def getRandom(self):
        if not self.songList:
            if self.viewPane.currentWidget() == self.viewPane.queue: return None
            self.songList = self.viewPane.currentWidget().getShownSongs()
        if self.songList:
            randomRow = random.randint(0, len(self.songList) - 1)
            return self.songList.pop(randomRow)
        return None

    def pause(self):
        self.songObject.pause()

    def stop(self):
        self.songObject.clearQueue()
        self.songObject.stop()
        if self.currentSong:
            self.previousSources.append(self.currentSong)
            self.currentSong = None
            return True
        return False

    def next(self):
        if self.queuedSources:
            self.play(self.queuedSources.pop(0))
        else:
            song = self.getRandom()
            if song:
                self.play(song)


    def previous(self):
        if self.songObject.currentTime() > Player.START_LEWAY_TIME:
            self.currentSong = None
            self.play(self.currentSong)
            return
        if self.previousSources:
            if self.stop():

                self.queuedSources.append(self.previousSources[len(self.previousSources) - 1]);
                self.previousSources.pop();

            self.currentSong = self.previousSources.pop()
            if not self.currentSong.getLocation():
                self.next()
                return
            source = Phonon.MediaSource(self.currentSong.getLocation())
            self.songObject.setCurrentSource(source)
            self.songObject.play()

    def getSources(self):
        return (self.previousSources, self.currentSong, self.queuedSources)

    def enqueueSong(self, song):
        self.queuedSources.append(song)
        self.viewPane.queue.resetFilter()

    def clearQueue(self):
        self.queuedSources = []
        self.viewPane.queue.resetFilter()

    def isPlaying(self):
        return (self.songObject.state() == Phonon.PlayingState)

    def aboutToFinish(self):
        self.next()
