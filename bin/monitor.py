#===============================================================================
# Needs to be written
#===============================================================================

#from watchdog.events import FileSystemEvent, FileSystemEventHandler
#
#import libmgr
#import mimetypes
#
#class SongFileEventHandler(FileSystemEventHandler):
#    def __init__(self, repository):
#        self.sqlaSession = libmgr.SqlaSession()
#        self.repository = repository
#
#    def dispatch(self, event):
#        if mimetypes.guess_type(event.src_path)[0] in libmgr.SUPPORTED_FILE_TYPES:
#            FileSystemEventHandler.dispatch(self, event)
#
#    def on_moved(self, event):
#        songFiles = self.sqlaSession.query(libmgr.SongFile) \
#                    .filter(libmgr.SongFile.location == event.src_path()).all()
#        for songFile in songFiles:
#            songFile.location = event.dest_path()
#        self.sqlaSession.commit()
#
#    def on_created(self, event):
#        self.repository.addSong(event.src_path(), libmgr.createSong(event.src_path()))
#
#    def on_deleted(self, event):
#        self.repository.removeSong(libmgr.createSong(event.src_path()))
#
#    def on_modified(self, event):
#        pass
