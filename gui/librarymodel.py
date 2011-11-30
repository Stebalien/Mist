__author__ = "Jonathan Allen"

from PySide import QtCore
from PySide.QtCore import Qt
from PySide import QtGui

import libmgr
import metaedit
from jonathan.dictools import *

DEFAULT_COLUMN_NAMES = ["TITLE", "ARTIST", "ALBUM", "GENRE"]

class Library(QtCore.QAbstractTableModel):
    def __init__(self, parent):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.sqlaSession = libmgr.SqlaSession()
        self.songs = OrderedDictionary()
        self.viewPane = parent
        self.columnNames = metaedit.GENERAL_TAGNAMES
        self.settings = QtCore.QSettings()
        libmgr.signalEmitter.songsAdded.connect(self.addSongs)
        libmgr.signalEmitter.songsChanged.connect(self.refreshCacheByIds)
        libmgr.signalEmitter.songsRemoved.connect(self.removeSongs)

    def flags(self, index):
        if not index.isValid():
            return
        return QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemIsEditable

    def rowCount(self, index = QtCore.QModelIndex()):
        return len(self.songs)

    def columnCount(self, index = QtCore.QModelIndex()):
        return len(self.columnNames)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self.columnNames):
                return self.columnNames[section].capitalize()
        return None

    def data(self, index, role = Qt.DisplayRole):

        if not index.isValid():
            return None

        if len(self.columnNames) > index.column() >= 0:
            if role == QtCore.Qt.ForegroundRole:
                song = self.songs.keyAt(index.row())
                if not song.getLocation(): return QtGui.QColor(150, 150, 150)
                return QtGui.QColor(50, 50, 50)
            if role == QtCore.Qt.FontRole:
                song = self.songs.keyAt(index.row())
                player = self.viewPane.mainWindow.player
                if song == player.getSources()[1]:
                    return QtGui.QFont("Garamond", 10, QtGui.QFont.Bold)
                else:
                    return QtGui.QFont("Garamond", 10)

            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                tagName = self.columnNames[index.column()]
                if tagName == "LOCATION":
                    song = self.songs.keyAt(index.row())
                    return song.getLocation(self.viewPane.getCurrentRepository())
                try: return self.songs[index.row()][tagName]
                except KeyError: return None
        return None

    def removeRows(self, position, rows = 1, index = QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows)
        del self.songs[position:position + rows]
        self.endRemoveRows()
        return True

    @QtCore.Slot(list)
    def addSongs(self, songIds):
        newSongs = set(self.sqlaSession.query(libmgr.Song).filter(libmgr.Song.id.in_(songIds)))
        newSongs.difference_update(set(self.songs.keys()))
        self.beginInsertRows(QtCore.QModelIndex(), 0, len(newSongs))
        self.songs.insert(0, OrderedDictionary.fromkeys(newSongs, {}))
        self.endInsertRows()
        self.refreshCacheByObjects(newSongs)
        return True

    @QtCore.Slot(list)
    def refreshCacheByIds(self, songIds):
        self.refreshCacheByObjects(self.sqlaSession.query(libmgr.Song).\
                    filter(libmgr.Song.id.in_(songIds)).all())

    def refreshCacheByObjects(self, songs):
        newData = dict([(song, dict([(tag.name, tag.value) for tag in song.tags] + [("TITLE", song.title)])) for song in songs])
        self.songs.update(newData)
        for song in songs:
            row = self.songs.index(song)
            self.dataChanged.emit(self.index(row, 0), self.index(row + 1, 1))

    @QtCore.Slot(list)
    def removeSongs(self, songIds):
        songs = self.sqlaSession.query(libmgr.Song).filter(libmgr.Song.id.in_(songIds))
        songs = set(songs).intersection(self.songs)
        for song in songs:
            position = self.songs.index(song)
            self.removeRows(position)
        return True

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole:
            song = self.songs.keyAt(index.row())
            tagName = self.columnNames[index.column()].upper()
            if tagName == "TITLE":
                song.setTitle(value)
                return True
            if tagName == "LOCATION":
                return False
            else:
                song.addTags([libmgr.getTag(tagName, value)], write = True)
            self.refreshCacheByObjects([song])
            return True
        return False

class TagLibrary(QtCore.QAbstractTableModel):
    def __init__(self, parent):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.sqlaSession = libmgr.SqlaSession()
        self.tags = OrderedDictionary()

        self.tagBrowser = parent
        libmgr.signalEmitter.tagsAdded.connect(self.addTags)
        libmgr.signalEmitter.tagsRemoved.connect(self.removeTags)
        libmgr.signalEmitter.tagsChanged.connect(self.refreshCacheByIds)

    def flags(self, index):
        return QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemIsEditable

    def rowCount(self, parent = QtCore.QModelIndex()):
        return len(self.tags)

    def columnCount(self, parent = QtCore.QModelIndex()):
        return 2

    def headerData(self, section, orientation, role = QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
                return self.tagBrowser.mainFilter.tagName

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if index.column() in (0, 1):
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if index.row() == 0:
                    return ["All", "All"][index.column()]
                return self.tags[index.row()][index.column()]
        return None

    def removeRows(self, position, rows = 1, index = QtCore.QModelIndex()):
        position += 1
        self.beginRemoveRows(QtCore.QModelIndex(), position, position + rows)
        del self.tags[position:position + rows]
        self.endRemoveRows()
        return True

    @QtCore.Slot(list)
    def addTags(self, tagIds):
        newTags = set(self.sqlaSession.query(libmgr.Tag).filter(libmgr.Tag.id.in_(tagIds)).all())
        newTags.difference_update(self.tags.keys())
        self.beginInsertRows(QtCore.QModelIndex(), 0, len(newTags))
        self.tags.insert(0, OrderedDictionary.fromkeys(newTags, (None, None)))
        self.endInsertRows()
        self.refreshCacheByObjects(newTags)
        return True

    @QtCore.Slot(list)
    def refreshCacheByIds(self, tagIds):
        tags = self.sqlaSession.query(libmgr.Song).\
                    filter(libmgr.Song.id.in_(tagIds)).all()
        self.refreshCacheByObjects(tags)

    def refreshCacheByObjects(self, tags):
        newData = dict([(tag, (tag.name, tag.value)) for tag in tags])
        self.tags.update(newData)
        for tag in tags:
            row = self.tags.index(tag)
            self.dataChanged.emit(self.index(row, 0), self.index(row + 1, 1))

    @QtCore.Slot(list)
    def removeTags(self, tagIds):
        tags = self.sqlaSession.query(libmgr.Tag).filter(libmgr.Tag.id.in_(tagIds))
        tags = set(tags).intersection(self.tags.keys())
        [self.removeRows(self.tagList.index(tag)) for tag in tags]
        return True

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole \
                    and index.column() == 0 and index.row() != 0:
            tag = self.tags.keyAt(index.row())
            tag.setValue(value)
            self.refreshCacheByObjects([tag])
            return True
        return False
