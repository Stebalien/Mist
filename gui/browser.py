__author__ = "Jonathan Allen"
__all__ = ["ViewPane", "TagBrowser"]

import os

from PySide import QtCore
from PySide import QtGui

import libmgr
from libmgr import *
import mainwindow
from metaedit import *
import librarymodel

from jonathan import dirtools


#===============================================================================
# Song Sort/Filter Models
#===============================================================================
class SongFilterModel(QtGui.QSortFilterProxyModel):
    filterChanged = QtCore.Signal()

    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.sqlaSession = SqlaSession()
        self.searchFilter = ""
        self.tagFilters = {}
        self.collection = None
        self.columns = set(["TITLE", "ARTIST", "ALBUM", "GENRE"])

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def showColumn(self, tagName):
        tagName = tagName.upper()
        if tagName not in self.library.columnNames:
            raise ValueError("invalid tagName: <{}>.".format(tagName))
        self.columns.remove(tagName)

    def hideColumn(self, tagName):
        tagName = tagName.upper()
        try:
            self.columns.remove(tagName)
        except KeyError:
            pass

    def addTagFilters(self, tagName, tagValues, filterId):
        tagName = tagName.upper()
        if tagName not in self.sourceModel().columnNames:
            raise ValueError("invalid tagName: <{}>.".format(tagName))
        self.tagFilters[filterId] = (tagName, tagValues)
        self.invalidateFilter()

    def removeTagFilter(self, filterId):
        if filterId in self.tagFilters:
            del self.tagFilters[filterId]
            self.invalidateFilter()

    def setSearchFilter(self, expression):
        self.searchFilter = expression.lower()
        self.invalidateFilter()

    def filterAcceptsColumn(self, sourceColumn, sourceRow):
        columnName = self.sourceModel().columnNames[sourceColumn]
        if columnName in self.columns:
            return True
        return False

    def filterAcceptsRow(self, sourceRow, sourceParent = QtCore.QModelIndex()):
        values = {}
        for column in self.columns:
            columnPosition = self.sourceModel().columnNames.index(column)
            index = self.sourceModel().index(sourceRow, columnPosition)
            values[column] = self.sourceModel().data(index)

        if not any([self.searchFilter in value.lower() for value in values.values() if value]):
            return False


        for (tagName, tagValues) in self.tagFilters.values():
            if "All" in tagValues:
                continue

            if all([values[tagName] != tagValue for tagValue in tagValues]):
                return False

        return True

    def invalidateFilter(self, *args, **kwargs):
        QtGui.QSortFilterProxyModel.invalidateFilter(self, *args, **kwargs)
        self.filterChanged.emit()


class CollectionFilter(SongFilterModel):
    def __init__(self, collection, parent):
        SongFilterModel.__init__(self, parent)
        self.collection = collection

    def filterAcceptsRow(self, sourceRow, sourceParent = QtCore.QModelIndex()):
        if SongFilterModel.filterAcceptsRow(self, sourceRow, sourceParent):
            try:
                song = self.sourceModel().songs.keyAt(sourceRow)
                if self.collection.__class__.__name__ == "Repository":
                    return song in self.collection or song.id in self.collection.pendingTransfers
                return song in self.collection
            except IndexError: pass
        return False

    def data(self, proxyIndex, role):
        sourceIndex = self.mapToSource(proxyIndex)
        if self.collection.__class__.__name__ == "Repository" \
                    and not self.collection.directory \
                    and role == QtCore.Qt.ForegroundRole:
            song = self.sourceModel().songs.keyAt(sourceIndex.row())
            if song.id in self.collection.pendingTransfers:
                (type, arguments) = self.collection.pendingTransfers[song.id]
                if type == "add":
                    return QtGui.QColor(16, 78, 139)
                if type == "remove":
                    return QtGui.QColor(126, 23, 31)
        return self.sourceModel().data(sourceIndex, role)

class QueueFilter(SongFilterModel):
    def __init__(self, player, parent):
        SongFilterModel.__init__(self, parent)
        self.player = player

    def lessThan(self, left, right):
        leftSong = self.sourceModel().songs.keyAt(left.row())
        rightSong = self.sourceModel().songs.keyAt(right.row())

        sources = self.player.getSources()
        sources = sources[0] + [sources[1]] + sources[2]
        leftIndex = sources.index(leftSong)
        rightIndex = sources.index(rightSong)
        return leftIndex < rightIndex

    def filterAcceptsRow(self, sourceRow, sourceParent = QtCore.QModelIndex()):
        if SongFilterModel.filterAcceptsRow(self, sourceRow, sourceParent):
            try:
                song = self.sourceModel().songs.keyAt(sourceRow)
                sources = self.player.getSources()
                if song in sources[0] or song in sources[2] or song == sources[1]:
                    return True
            except IndexError: pass
        return False

    def data(self, proxyIndex, role):
        sourceIndex = self.mapToSource(proxyIndex)
        if role == QtCore.Qt.ForegroundRole:
            song = self.sourceModel().songs.keyAt(sourceIndex.row())
            if song in self.player.getSources()[0]:
                return QtGui.QColor(150, 150, 150)
        return self.sourceModel().data(sourceIndex, role)


class Browser(QtGui.QTableView):
    DEFAULT_COLUMN_WIDTH = 700
    songClicked = QtCore.Signal(libmgr.Song, list)

    def __init__(self, library, parent):
        QtGui.QTableView.__init__(self, parent)
        self.sqlaSession = SqlaSession()

        self.mainFilter = SongFilterModel(self)
        self.library = library

        self.setup()

    def setup(self):
        self.initialized = True
        self.mainFilter.setSourceModel(self.library)

        self.setModel(self.mainFilter)

        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(False)
        self.verticalHeader().hide()
        self.setEditTriggers(QtGui.QAbstractItemView.SelectedClicked)
        self.setAcceptDrops(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #self.loadSettings()

        self.doubleClicked.connect(self.receiveDoubleClicked)



    """
    def loadSettings(self):
        self.settings = QtCore.QSettings()
        self.settings.beginGroup("Browser/Columns")
        for i, columnName in enumerate(self.library.columnNames[:-1]):
            self.setColumnWidth(i, int(self.settings.value(columnName, Browser.DEFAULT_COLUMN_WIDTH)))
        self.settings.endGroup()
    """

    def getCurrentSelection(self):
        indices = self.selectionModel().selectedRows()
        return [self.library.songs.keyAt(self.mapToSource(index).row()) for index in indices]

    def getShownSongs(self):
        songs = []
        for row in range(self.library.rowCount()):
            if self.mainFilter.filterAcceptsRow(row):
                song = self.library.songs.indexAt(row)
                if song.getLocation():
                    songs.append(song)
        return songs

    def getPosition(self, song):
        try:
            row = self.library.songs.index(song)
            return self.mapFromSource(self.library.index(row, 0)).row()
        except ValueError:
            return -1

    def rowCount(self):
        return reduce(lambda x, y: x + y,
                      [self.mainFilter.filterAcceptsRow(row, QtCore.QModelIndex())
                       for row in range(self.library.rowCount())], 0)

    def getSong(self, proxyRow):
        sourceRow = self.mapToSource(self.model().index(proxyRow, 0)).row()
        return self.library.songs.keyAt(sourceRow)

    def mapFromSource(self, index):
        return self.mainFilter.mapFromSource(index)

    def mapToSource(self, index):
        return self.mainFilter.mapToSource(index)

    @QtCore.Slot(QtCore.QModelIndex)
    def receiveDoubleClicked(self, index):
        row = self.mapToSource(index).row()
        song = self.library.songs.keyAt(row)
        self.songClicked.emit(song, self.getShownSongs())

    def resetFilter(self):
        self.mainFilter.invalidate()

class CollectionBrowser(Browser):

    def __init__(self, library, collection, parent):
        Browser.__init__(self, library, parent)
        self.collection = collection
        self.mainFilter = CollectionFilter(self.collection, self);
        self.setup()

    def dragEnterEvent(self, event):
        if self.collection.__class__.__name__ != "Repository":
            event.ignore()
            return
        location = event.mimeData().text().replace("file://", "").replace("%20", " ").strip()
        if os.path.exists(location):
            if os.path.isdir(location): event.accept()
            else:
                try:
                    Metadata(location)
                    event.accept()
                except FileError:
                    event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if self.collection.__class__.__name__ != "Repository":
            return
        location = event.mimeData().text().replace("file://", "").replace("%20", " ").strip()
        if os.path.isdir(location):
            for fileName in dirtools.search(location, libmgr.SUPPORTED_FILE_TYPES, relative = False):
                song = libmgr.getSongByLocation(fileName)
                if song:
                    self.collection.addSong(fileName, song, keepOriginal = True)
        if os.path.isfile(location):
            song = libmgr.getSongByLocation(location)
            if song:
                self.collection.addSong(location, song, keepOriginal = True)


class QueueBrowser(Browser):
    def __init__(self, library, player, parent):
        Browser.__init__(self, library, parent)
        self.mainFilter = QueueFilter(player, self)
        self.player = player

        self.setup()

        self.setSortingEnabled(False)

class ViewPane(QtGui.QStackedWidget):
    songClicked = QtCore.Signal(libmgr.Song, list)
    filterChanged = QtCore.Signal()

    def __init__(self, parent):
        QtGui.QStackedWidget.__init__(self, parent)
        self.browsers = {}
        self.mainWindow = parent
        self.sqlaSession = SqlaSession()
        self.library = librarymodel.Library(self)

        self.viewPaneContextMenu = QtGui.QMenu(self)
        self.viewPaneContextMenu.addAction(self.mainWindow.ui.deleteSongAction)
        self.viewPaneContextMenu.addMenu(self.mainWindow.ui.addToRepositoryMenu)
        self.viewPaneContextMenu.addMenu(self.mainWindow.ui.addToPlaylistMenu)
        self.viewPaneContextMenu.addAction(self.mainWindow.ui.enqueueSongsAction)

        self.queueContextMenu = QtGui.QMenu(self)
        self.queueContextMenu.addAction(self.mainWindow.ui.clearSongQueueAction)

        @QtCore.Slot(QtCore.QPoint)
        def showContextMenu(point):
            if self.currentWidget() == self.queue:
                self.queueContextMenu.exec_(self.mapToGlobal(point))
            else:
                self.viewPaneContextMenu.exec_(self.mapToGlobal(point))

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(showContextMenu)

    def setup(self):
        self.allSongs = Browser(self.library, self)
        self.allSongs.songClicked.connect(self.songClicked)
        self.addWidget(self.allSongs)

        self.queue = QueueBrowser(self.library, self.mainWindow.player, self)
        self.queue.songClicked.connect(self.songClicked)
        self.addWidget(self.queue)

        self.setCurrentWidget(self.allSongs)

    def addCollection(self, collection):
        if collection not in self.browsers:
            collectionBrowser = self.browsers[collection] = CollectionBrowser(self.library, collection, self)
            collectionBrowser.songClicked.connect(self.songClicked)
            self.addWidget(collectionBrowser)

    def getCurrentRepository(self):
        if self.currentWidget().__class__.__name__ == "CollectionBrowser" \
                    and self.currentWidget().collection.__class__.__name__ == "Repository":
                return self.currentWidget().collection
        else:
            return None

    def enqueueSelection(self):
        for song in self.currentWidget().getCurrentSelection():
            self.mainWindow.player.enqueueSong(song)

    def deleteCurrentCollection(self):
        if self.currentWidget() in (self.allSongs, self.queue): return

        collection = self.currentWidget().collection
        collection.delete()

    def getBrowser(self, collection):
        if collection in self.browsers:
            return self.browsers[collection]
        return None

    def removeCollection(self, collection):
        if collection in self.browsers:
            self.removeWidget(self.browsers[collection])
            del self.browsers[collection]

    def showCollection(self, collection):
        self.setCurrentWidget(self.browsers[collection])

    @QtCore.Slot(libmgr.Playlist)
    def addSelectionToPlaylist(self, playlist):
        playlist.addSongs(self.currentWidget().getCurrentSelection())

    @QtCore.Slot(libmgr.Repository)
    def addSelectionToRepository(self, repository):
        songs = self.currentWidget().getCurrentSelection()
        libmgr.signalEmitter.longTask.emit("Adding Songs to Repository", len(songs))
        for i, song in enumerate(songs):
            if song not in repository:
                repository.addSong(song.getLocation(), song, keepOriginal = True)
            libmgr.signalEmitter.longTaskIncrement.emit(i)
        libmgr.signalEmitter.longTaskDone.emit()

    def deleteSelection(self):
        songs = self.currentWidget().getCurrentSelection()
        if self.currentWidget() == self.queue:
            for song in songs:
                self.mainWindow.player.queuedSelection.remove(song)
                self.queue.resetFilter()

        if self.currentWidget() == self.allSongs:
            for song in songs:
                song.delete()

        else:
            for song in songs:
                self.currentWidget().collection.removeSongs([song])

    def selectSong(self, song):
        row = self.currentWidget().getPosition(song)
        if row != -1:
            self.currentWidget().selectRow(row)

    @QtCore.Slot(libmgr.Repository)
    @QtCore.Slot(libmgr.Playlist)
    def updateCollection(self, collection):
        if self.currentWidget() == self.allSongs: return
        if self.currentWidget().collection == collection:
            self.currentWidget().resetFilter()


class TagFilterModel(QtGui.QSortFilterProxyModel):

    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self.sqlaSession = SqlaSession()
        self.tagName = ""
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def filterTag(self, tagName):
        self.tagName = tagName.upper()
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if sourceRow < len(self.sourceModel().tags):
            if sourceRow == 0: return True
            tagName = self.sourceModel().data(self.sourceModel().index(sourceRow, 0))
            if tagName == self.tagName:
                return True
        return False

    def lessThan(self, left, right):
        leftValue = self.sourceModel().data(left)
        rightValue = self.sourceModel().data(right)
        if leftValue == "All":
            return True
        elif rightValue == "All":
            return False
        left = self.sourceModel().index(left.row(), 1)
        right = self.sourceModel().index(right.row(), 1)
        return QtGui.QSortFilterProxyModel.lessThan(self, left, right)


class TagBrowser(QtGui.QTableView):
    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self.sqlaSession = SqlaSession()

        self.library = librarymodel.TagLibrary(self)
        self.mainFilter = TagFilterModel(self)
        self.mainFilter.setSourceModel(self.library)
        self.setModel(self.mainFilter)

        self.setShowGrid(False)
        self.hideColumn(0)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.mainWindow = parent
        self.horizontalHeader().setStretchLastSection(True)
        self.library.dataChanged.connect(self.resetFilter)
        self.verticalHeader().hide()

        self.mainWindow.ui.renameTagsAction.triggered.connect(self.renameTags)
        self.mainWindow.ui.deleteTagsAction.triggered.connect(self.deleteTags)

        self.tagBrowserContextMenu = QtGui.QMenu(self)
        self.tagBrowserContextMenu.addAction(self.mainWindow.ui.renameTagsAction)
        self.tagBrowserContextMenu.addAction(self.mainWindow.ui.deleteTagsAction)

        @QtCore.Slot(QtCore.QPoint)
        def showContextMenu(point):
            self.tagBrowserContextMenu.exec_(self.mapToGlobal(point))

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(showContextMenu)

    def deleteTags(self):
        [tag.delete() for tag in self.getCurrentSelection()]

    def renameTags(self):
        dialog = mainwindow.renameTagsDialog()
        if not dialog.exec_(): return
        newValue = dialog.ui.tagValueInput.text()
        tag = libmgr.getTag(self.mainFilter.tagName, newValue)
        print self.getCurrentSelection()
        [tag.merge(oldTag) for oldTag in self.getCurrentSelection()]

    def getCurrentSelection(self):
        return [self.library.tags.keyAt(self.mainFilter.mapToSource(index).row()) for index in self.selectedIndexes()]

    def resetFilter(self):
        self.mainFilter.invalidateFilter()
        self.mainFilter.sort(0)
