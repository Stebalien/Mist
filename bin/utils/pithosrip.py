#!/usr/bin/python

import urllib
import subprocess
import os

import mist.tagtools as tagtools

def download_song(song):
    temp_file = '/tmp/{0}'.format(song.title)
    track_file = '/home/jonathan/Music/Add to Library/{0}.ogg'.format(song.title)
    urllib.urlretrieve(song.audioUrl,temp_file)
    metadata = {}
    metadata['TITLE'] = song.title
    metadata['ALBUM'] = song.album
    metadata['ARTIST'] = song.artist
    
    command = '/usr/bin/ffmpeg -i \'{0}\' -f wav - | /usr/bin/oggenc - -q 6 -o \'{1}\''.format(temp_file,track_file) 
    subprocess.call(command,shell=True)
    song_tag = tagtools.tag_handler(track_file)
    song_tag.write(metadata)
    os.remove(temp_file)
