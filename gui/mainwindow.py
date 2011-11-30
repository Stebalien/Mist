__author__ = "jonathan"

import sys
import os

modulePath = os.path.dirname(os.path.abspath(__file__))
mistPath = os.path.split(modulePath)[0]

sys.path.append(mistPath)
sys.path.append(os.path.join(mistPath, "bin"))
sys.path.append(os.path.join(mistPath, "gui"))

from PySide import QtCore
from PySide import QtGui
from PySide.phonon import Phonon

from forms.ui_mainwindow import Ui_mainwindow
from forms.ui_addrepositorydialog import Ui_addRepositoryDialog
from forms.ui_addplaylistdialog import Ui_addPlaylistDialog
from forms.ui_renametagsdialog import Ui_renameTagsDialog

import libmgr
from libmgr import *
import browser
import player
from metaedit import *
from jonathan import dirtools

#===============================================================================
# Dialog Windows
#===============================================================================
class addPlaylistDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_addPlaylistDialog()
        self.ui.setupUi(self)


class addRepositoryDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_addRepositoryDialog()
        self.ui.setupUi(self)


class renameTagsDialog(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_renameTagsDialog()
        self.ui.setupUi(self)


class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self, None)
        self.sqlaSession = SqlaSession()

        self.ui = Ui_mainwindow()
        self.ui.setupUi(self)

        self.viewPane = browser.ViewPane(self)
        self.tagBrowser1 = browser.TagBrowser(self)
        self.tagBrowser1.selectRow(0)
        self.tagBrowser2 = browser.TagBrowser(self)
        self.tagBrowser2.selectRow(0)
        self.setupPlayer()
        self.viewPane.setup()

        self.setupCentralWidget()
        self.setupLeftDock()
        self.setupActions()

        self.loadSettings()

        #libmgr.dump("/home/jonathan/Desktop/dump.txt")

    def closeEvent(self, event):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()
        self.settings.beginGroup("ViewPane")
        self.settings.setValue("splitter", self.centralSplitter.saveState())
#        self.settings.beginGroup("")
#        columnNames = self.viewPane.browser.getColumnNames
#        self.settings.setValue("activated", self.viewPane.browser.getColumnNames)
#        for i, columnName in enumerate(self.viewPane.library.columnNames[:-1]):
#            self.settings.setValue(columnName, self.browser.columnWidth(i))
        self.settings.endGroup()
        event.accept()

    def loadSettings(self):
        self.settings = QtCore.QSettings()
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size", QtCore.QSize(400, 400)))
        self.move(self.settings.value("pos", QtCore.QPoint(200, 200)))
        self.settings.endGroup()
        self.settings.beginGroup("ViewPane")
        self.centralSplitter.restoreState(self.settings.value("splitter"))
        self.settings.endGroup()

    def setupActions(self):
        self.ui.playPauseAction.setShortcut("Space")
        self.ui.playPauseAction.setText("Play")
        self.ui.playPauseAction.setIcon(QtGui.QIcon(resources.filePath("icons/media-playback-start.svg")))
        self.ui.nextAction.setShortcut("Ctrl+N")
        self.ui.nextAction.setIcon(QtGui.QIcon(resources.filePath("icons/media-skip-forward.svg")))
        self.ui.previousAction.setShortcut("Ctrl+R")
        self.ui.previousAction.setIcon(QtGui.QIcon(resources.filePath("icons/media-skip-backward.svg")))
        self.ui.quitAction.setShortcuts(QtGui.QKeySequence.Quit)

        self.ui.quitAction.triggered.connect(self.close)

        self.ui.newPlaylistAction.triggered.connect(self.createPlaylist)
        self.ui.newRepositoryAction.triggered.connect(self.createRepository)
        self.ui.deleteCollectionAction.triggered.connect(self.viewPane.deleteCurrentCollection)
        self.ui.modifyCollectionAction.triggered.connect(self.modifyCurrentCollection)
        self.ui.importSongAction.triggered.connect(self.importSongs)
        self.ui.importDirectoryAction.triggered.connect(self.importDirectory)
        self.ui.deleteSongAction.triggered.connect(self.viewPane.deleteSelection)

    def setupCentralWidget(self):
        self.centralSplitter = QtGui.QSplitter()
        self.centralSplitter.setOrientation(QtCore.Qt.Vertical)
        tagBrowserWidget = QtGui.QWidget()
        tagBrowserLayout = QtGui.QHBoxLayout()
        tagBrowserLayout.addWidget(self.tagBrowser1)
        tagBrowserLayout.addWidget(self.tagBrowser2)
        tagBrowserWidget.setLayout(tagBrowserLayout)
        self.centralSplitter.addWidget(tagBrowserWidget)
        self.centralSplitter.addWidget(self.viewPane)
        self.setCentralWidget(self.centralSplitter)

        self.viewPane.filterChanged.connect(self.updateSongCount)

        """Connect Tag browsers to song browser"""
        def emitTagClicked1(index):
            tagValues = [self.tagBrowser1.mainFilter.data(index) for index in self.tagBrowser1.selectedIndexes()]
            tagName = self.tagBrowser1.mainFilter.tagName
            self.viewPane.currentWidget().mainFilter.addTagFilters(tagName, tagValues, 1)

        self.tagBrowser1.clicked.connect(emitTagClicked1)

        def emitTagClicked2(index):
            tagValues = [self.tagBrowser2.mainFilter.data(index) for index in self.tagBrowser2.selectedIndexes()]
            tagName = self.tagBrowser2.mainFilter.tagName
            self.viewPane.currentWidget().mainFilter.addTagFilters(tagName, tagValues, 2)

        self.tagBrowser2.clicked.connect(emitTagClicked2)

    def setupLeftDock(self):
        self.ui.songCountLabel.hide()
        self.ui.songInfo.hide()

        self.ui.collectionsList.setSortingEnabled(False)
        self.ui.collectionsList.header().hide()

        self.playlistsList = QtGui.QTreeWidgetItem(self.ui.collectionsList)
        self.playlistsList.setText(0, "Playlists")
        self.playlistsList.setExpanded(True)

        self.repositoriesList = QtGui.QTreeWidgetItem(self.ui.collectionsList)
        self.repositoriesList.setText(0, "Repositories")
        self.repositoriesList.setExpanded(True)

        self.showLibrary = QtGui.QTreeWidgetItem(self.ui.collectionsList)
        self.showLibrary.setText(0, "Library")

        self.showQueue = QtGui.QTreeWidgetItem(self.ui.collectionsList)
        self.showQueue.setText(0, "Queue")

        items = [self.showLibrary, self.repositoriesList, self.playlistsList, self.showQueue]
        for item in items:
            item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.ui.collectionsList.insertTopLevelItems(0, items)

        self.ui.collectionsList.itemClicked.connect(self.showCollection)

        signalEmitter.playlistAdded.connect(self.addPlaylist)
        signalEmitter.playlistRemoved.connect(self.removePlaylist)
        signalEmitter.repositoryAdded.connect(self.addRepository)
        signalEmitter.repositoryRemoved.connect(self.removeRepository)
        signalEmitter.repositoryDisabled.connect(self.disableRepository)

        @QtCore.Slot(int)
        def emitRepositoryChange(id):
            repository = sqlaSession.query(Repository).get(id)
            self.viewPane.updateCollection(repository)

        signalEmitter.repositoryChanged.connect(emitRepositoryChange)

        @QtCore.Slot(int)
        def emitPlaylistChange(id):
            playlist = sqlaSession.query(Playlist).get(id)
            self.viewPane.updateCollection(playlist)

        signalEmitter.playlistChanged.connect(emitPlaylistChange)

        self.ui.progressBar.setVisible(False)
        self.ui.taskLabel.setVisible(False)
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setFormat("%v/%m")

        signalEmitter.longTask.connect(self.startLongTask)
        signalEmitter.longTaskIncrement.connect(self.ui.progressBar.setValue)
        signalEmitter.longTaskDone.connect(self.endLongTask)

        def emitUserSeach():
            self.viewPane.currentWidget().mainFilter.setSearchFilter(self.ui.searchInput.text())
        self.ui.searchInput.textChanged.connect(emitUserSeach)

        """Populate tag name combo boxes"""
        tagBrowserNames = [tagName.capitalize() for tagName in GENERAL_TAGNAMES if tagName != "Title"]
        tagBrowserNames.sort()
        self.ui.tagNameFilter1.addItems(tagBrowserNames)
        self.ui.tagNameFilter2.addItems(tagBrowserNames)

        def changeTagBrowser1():
            self.tagBrowser1.selectRow(0)
            self.viewPane.currentWidget().mainFilter.removeTagFilter(1)
        self.ui.tagNameFilter1.currentIndexChanged.connect(changeTagBrowser1)
        self.ui.tagNameFilter1.currentIndexChanged.connect(self.tagBrowser1.mainFilter.filterTag)

        def changeTagBrowser2():
            self.tagBrowser2.selectRow(0)
            self.viewPane.currentWidget().mainFilter.removeTagFilter(2)
        self.ui.tagNameFilter2.currentIndexChanged.connect(changeTagBrowser2)
        self.ui.tagNameFilter2.currentIndexChanged.connect(self.tagBrowser2.mainFilter.filterTag)

        self.tagBrowser1.mainFilter.filterTag(self.ui.tagNameFilter1.currentText())
        index = self.ui.tagNameFilter2.findText("Genre")
        self.ui.tagNameFilter2.setCurrentIndex(index)

        """Collections browser context menu"""
        self.collectionsContextMenu = QtGui.QMenu(self.ui.collectionsList)
        self.collectionsContextMenu.addAction(self.ui.newPlaylistAction)
        self.collectionsContextMenu.addAction(self.ui.newRepositoryAction)
        self.collectionsContextMenu.addAction(self.ui.modifyCollectionAction)
        self.collectionsContextMenu.addAction(self.ui.deleteCollectionAction)

        self.ui.collectionsList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.collectionsList.customContextMenuRequested.connect(self.showCollectionsContextMenu)

    @QtCore.Slot(QtCore.QPoint)
    def showCollectionsContextMenu(self, point):
        self.collectionsContextMenu.exec_(self.ui.collectionsList.mapToGlobal(point))

    def modifyCurrentCollection(self):
        if self.viewPane.currentWidget().__class__.__name__ != "CollectionBrowser": return

        collection = self.viewPane.currentWidget().collection

        if collection.__class__.__name__ == "Repository":
            dialog = addRepositoryDialog()
            dialog.setWindowTitle("Modify Repository")
            dialog.ui.nameInput.setText(collection.name)
            dialog.ui.locationInput.setText(collection.location)
            if collection.monitored:
                dialog.ui.monitoredInput.setCheckState(QtCore.Qt.Checked)
            if collection.managed:
                dialog.ui.managedInput.setCheckState(QtCore.Qt.Checked)
            if not dialog.exec_(): return
            name = dialog.ui.nameInput.text()
            location = dialog.ui.locationInput.text()
            location = location.strip().replace("file://", "").replace("%20", " ")
            monitored = dialog.ui.monitoredInput.isChecked()
            managed = dialog.ui.managedInput.isChecked()
            collection.setManaged(managed)
            collection.setMonitored(monitored)
            collection.setLocation(location)

        if collection.__class__.__name__ == "Playlist":
            dialog = addPlaylistDialog()
            dialog.setWindowTitle("Modify Playlist")
            dialog.ui.nameInput.setText(collection.name)
            if not dialog.exec_(): return
            name = dialog.ui.nameInput.text()

        collection.setName(name)

    def createRepository(self):
        dialog = addRepositoryDialog()
        if not dialog.exec_(): return
        name = dialog.ui.nameInput.text()
        location = dialog.ui.locationInput.text()
        location = location.strip().replace("file://", "").replace("%20", " ")
        monitored = dialog.ui.monitoredInput.isChecked()
        managed = dialog.ui.managedInput.isChecked()
        libmgr.createRepository(name, location, monitored = monitored, managed = managed)

    def createPlaylist(self):
        dialog = addPlaylistDialog()
        if not dialog.exec_(): return
        libmgr.createPlaylist(dialog.ui.nameInput.text())

    def importSongs(self, repository = None):
        if not repository: repository = self.viewPane.getCurrentRepository()
        if not repository: return
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Import Songs",
                QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.MusicLocation),
                "Media Files(*.mp3 *.m4a *.ogg)")
        for fileName in fileNames[0]:
            song = libmgr.getSongByLocation(fileName)
            repository.addSong(fileName, song, keepOriginal = True)

    def importDirectory(self, repository = None):
        if not repository: repository = self.viewPane.getCurrentRepository()
        if not repository: return
        dirName = QtGui.QFileDialog.getExistingDirectory(self, "Import Song Directory",
                QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.MusicLocation))
        if not dirName: return
        for fileName in dirtools.search(dirName, libmgr.SUPPORTED_FILE_TYPES, relative = False):
            song = libmgr.getSongByLocation(fileName)
            repository.addSong(fileName, song, keepOriginal = True)

    @QtCore.Slot(Song)
    def songPlaying(self, song):
        self.ui.playPauseAction.setText("Pause")
        self.ui.playPauseAction.setIcon(QtGui.QIcon(resources.filePath("icons/media-playback-pause.svg")))
        self.ui.playPauseAction.triggered.disconnect(self.player.play)
        self.ui.playPauseAction.triggered.connect(self.player.pause)
        metadata = song.getMetadata()
        self.ui.songTitleLabel.setText(song.title)
        self.ui.songArtistLabel.setText("by {}".format(metadata["ARTIST"]))
        self.ui.songAlbumLabel.setText("on {}".format(metadata["ALBUM"]))
        self.ui.songInfo.show()
        self.viewPane.queue.resetFilter()

    def songPaused(self):
        self.ui.playPauseAction.setText("Play")
        self.ui.playPauseAction.setIcon(QtGui.QIcon(resources.filePath("icons/media-playback-start.svg")))
        self.ui.playPauseAction.triggered.disconnect(self.player.pause)
        self.ui.playPauseAction.triggered.connect(self.player.play)

    def updateSongCount(self):
        self.ui.songCountLabel.show()
        self.ui.songCountLabel.setText("Songs: {}\t".format(self.viewPane \
                                                          .currentWidget() \
                                                          .rowCount()))

    @QtCore.Slot(str, int)
    def startLongTask(self, name, ticks):
        self.ui.progressBar.reset()
        self.ui.progressBar.setMaximum(ticks)
        self.ui.progressBar.setVisible(True)
        self.ui.taskLabel.setText(name)
        self.ui.taskLabel.setVisible(True)

    def endLongTask(self):
        self.ui.progressBar.setVisible(False)
        self.ui.taskLabel.setVisible(False)
        self.ui.progressBar.reset()

    def setupPlayer(self):
        self.player = player.Player(self.viewPane, self)

        self.player.songPlaying.connect(self.songPlaying)

        self.viewPane.songClicked.connect(self.player.play)
        self.player.songPlaying.connect(self.viewPane.selectSong)
        self.player.songPaused.connect(self.songPaused)
        seekSlider = Phonon.SeekSlider(self.ui.playbackControlsBar)
        self.ui.playbackControlsBar.addWidget(seekSlider)
        seekSlider.setMediaObject(self.player.songObject)

        self.ui.playPauseAction.triggered.connect(self.player.play)
        self.ui.previousAction.triggered.connect(self.player.previous)
        self.ui.nextAction.triggered.connect(self.player.next)
        self.ui.enqueueSongsAction.triggered.connect(self.viewPane.enqueueSelection)
        self.ui.clearSongQueueAction.triggered.connect(self.player.clearQueue)

    @QtCore.Slot(QtGui.QListWidgetItem, int)
    def showCollection(self, item, column):
        if item is self.playlistsList or item is self.repositoriesList: return
        elif item is self.showLibrary:
            self.viewPane.setCurrentWidget(self.viewPane.allSongs)
        elif item is self.showQueue:
            self.viewPane.setCurrentWidget(self.viewPane.queue)
        elif item.parent() is self.playlistsList:
            collection = self.sqlaSession.query(Playlist) \
                        .filter(Playlist.name == item.text(0)).first()
            self.viewPane.showCollection(collection)
        elif item.parent() is self.repositoriesList:
            collection = self.sqlaSession.query(Repository) \
                        .filter(Repository.name == item.text(0)).first()
            self.viewPane.showCollection(collection)

        self.viewPane.currentWidget().mainFilter.removeTagFilter(2)
        self.viewPane.currentWidget().mainFilter.removeTagFilter(1)
        self.viewPane.currentWidget().resetFilter()

    @QtCore.Slot(int)
    def addPlaylist(self, playlistId):
        playlist = sqlaSession.query(Playlist).get(playlistId)
        self.viewPane.addCollection(playlist)
        if not self.ui.collectionsList.findItems(playlist.name, QtCore.Qt.MatchExactly):
            item = QtGui.QTreeWidgetItem(self.playlistsList)
            item.setText(0, playlist.name)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.playlistsList.addChild(item)

            def addSelection():
                self.viewPane.addSelectionToPlaylist(playlist)

            addToPlaylistAction = self.ui.addToPlaylistMenu.addAction(playlist.name)
            addToPlaylistAction.triggered.connect(addSelection)

    @QtCore.Slot(int)
    def removePlaylist(self, playlistName):
        for i in range(self.playlistsList.childCount()):
            if self.playlistsList.child(i).text(0) == playlistName:
                self.playlistsList.takeChild(i)
        actions = self.ui.addToPlaylistMenu.actions()
        for action in actions:
            if action.text() == playlistName:
                self.ui.addToPlaylistMenu.removeAction(action)

    @QtCore.Slot(int)
    def addRepository(self, repositoryId):
        repository = sqlaSession.query(Repository).get(repositoryId)
        self.viewPane.addCollection(repository)
        if not any([repository.name == self.repositoriesList.child(index).text(0) for \
                    index in range(self.repositoriesList.childCount())]):
            item = QtGui.QTreeWidgetItem(self.repositoriesList)
            item.setText(0, repository.name)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.repositoriesList.addChild(item)

            def addSelection():
                self.viewPane.addSelectionToRepository(repository)

            addToRepositoryAction = self.ui.addToRepositoryMenu.addAction(repository.name)
            addToRepositoryAction.triggered.connect(addSelection)

    @QtCore.Slot(int)
    def disableRepository(self, repositoryId):
        repository = self.sqlaSession.query(Repository).get(repositoryId)
        for i in range(self.repositoriesList.childCount()):
            if self.repositoriesList.child(i).text(0) == repository.name:
                self.repositoriesList.child(i).setDisabled(True)

        if not self.viewPane.getBrowser(repository):
            self.addRepository(repository.id)

    @QtCore.Slot(int)
    def removeRepository(self, repositoryName):
        for i in range(self.repositoriesList.childCount()):
            try:
                if self.repositoriesList.child(i).text(0) == repositoryName:
                    self.repositoriesList.takeChild(i)
            except AttributeError: continue
        actions = self.ui.addToRepositoryMenu.actions()
        for action in actions:
            if action.text() == repositoryName:
                self.ui.addToRepositoryMenu.removeAction(action)


if __name__ == "__main__":

    resources = QtCore.QDir(os.path.join(mistPath, "resources"))
    libmgr.setupSqlAlchemy(resources.filePath("database.db"))
    sqlaSession = SqlaSession()

    app = QtGui.QApplication(sys.argv)

    styleSheet = open(resources.filePath("mainstylesheet.qss")).read()

    app.setOrganizationName("Jonathan")
    app.setApplicationName("Mist")
    app.setStyleSheet(styleSheet)
    mainWindow = MainWindow()
    mainWindow.setWindowIcon(QtGui.QIcon(resources.filePath("icons/package-manager-icon.svg")))

    mainWindow.show()
    libmgr.workerQueue.put([libmgr.loadAllSongs, ()])
    libmgr.workerQueue.put([libmgr.loadAllTags, ()])
    libmgr.loadAllRepositories()
    libmgr.loadAllPlaylists()

    libmgr.dump("/home/jonathan/Desktop/mist_db.txt")
    sys.exit(app.exec_())
