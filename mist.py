#! /usr/bin/python

import cms

if __name__ == "__main__":
    user_id = 'jonathan'
    cms.initialize_sql('/usr/local/mist')
    new_library = cms.ManageLibrary(user_id)
    new_library.create('/home/jonathan/Mist Library','main')
    libraries = {}
    for library in cms.get_libraries():
        libraries[library.id] = cms.ManageLibrary(user_id)
        libraries[library.id].load(library.id)
        libraries[library.id].add('/home/jonathan/Music/Acceptance/Phantoms/Different.m4a')
    song_id = libraries[1].get_songs()[0]
    cms.change_tag(song_id,'genre','Rock',write_tag=True)
    cms.change_tag(song_id,'artist','Test artist',write_tag=True)
    new_playlist = cms.ManagePlaylist()
    new_playlist.create('Favorite Songs')
    new_playlist.add(1)
    #cms.get_song_data(song_id)
    cms.dump()
    
