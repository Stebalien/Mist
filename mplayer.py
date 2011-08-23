#!/usr/bin/python

import subprocess
import sys
import os
import thread
import mimetypes

import jallen.dirsearch

commands = {
    'pause': 'pause',
    'get': 'get_property',
    'increment': 'step_property',
    'set': 'set_property',
    'dvdnavigation': 'dvdnav',
    'loadfile': 'loadfile',
    'framestep': 'frame_step',
    'seek': 'seek' #Follow value with (0:Relative time seek, 1:Absolute % seek, 2:Absolute time seek)
}

properties = {
    'pause': 'pause',
    'play': 'pause',
    'speed': 'speed',
    'length': 'length',
    'percent': 'percent_pos',
    'filename': 'filename',
    'position': 'time_pos',
    'volume': 'volume',
    'balance': 'balance',
    'mute': 'mute',
    'fullscreen': 'fullscreen',
    'ontop': 'ontop',
    'gamma': 'gamma',
    'brightness': 'brightness',
    'contrast': 'contrast',
    'saturation': 'saturation',
    'hue': 'hue',
    'width': 'width',
    'height': 'height',
    'aspect': 'aspect',
    'metadata':'metadata'
}

class MPlayer():
    
    def __init__(self):
        
        self.player = False
        self.info = []
        self.paused = True
        
    def playSong(self, content): 
        self.content = content
        if self.player:
            command('loadfile', content)
            return None
        self.player = subprocess.Popen(["/opt/local/bin/mplayer", '-slave', '-quiet', self.content], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.paused = False
        self.getFeedback()

    def command(self, command, args=[]):
        if command == 'get':
            return args[0] + " = " + self.getproperty(*args)
        elif command == 'set':
            self.setproperty(*args)
            return args[0] + " set to: " + args[1]
        elif command == 'increment':
            self.incproperty(*args)
            return args[0] + " incremented by: " + args[1]
        fullcommand = commands[command]
        for arg in args:
            fullcommand += " " + arg
        fullcommand += "\n"
        self.player.stdin.write(fullcommand)
        return ""
    
    def pause(self):
        self.command('pause')
        self.paused = True
    def play(self):
        self.command('pause')
        self.paused = False
    def setproperty(self, prop, value):
        if not self.player:
            return "No Song"
        fullcommand = " ".join([commands['set'], properties[prop], str(value)]) + "\n"
        self.player.stdin.write(fullcommand)

    def incproperty(self, prop, inc=0):
    
        direction = 1
        if inc < 0:
            direction = -1
            inc = abs(inc)
        fullcommand = " ".join([commands['increment'], properties[prop], str(inc), str(direction)]) + "\n"
        self.player.stdin.write(fullcommand)

    def getproperty(self, prop):
        
        if not self.player:
            return None
        try:
            fullcommand = " ".join([commands['get'], properties[prop]])+"\n"
        except KeyError:
            print "Invalid Command"
        self.player.stdin.write(fullcommand)
        feedback = self.player.stdout.readline()
        feedback = feedback.split("=")[1].strip()
        return feedback
             
    def stop(self):
        
        if self.player:
            self.player.terminate()
            self.player = False
        
    def getFeedback(self):
        
        self.info = []
        while True:
            feed = self.player.stdout.readline()
            self.info.append(feed)
            if 'Starting playback...' in feed:
               break                
if __name__ == '__main__':
    content = sys.argv[1]
    newplayer = MPlayer()
    newplayer.playSong(content)
    playlist = []
    data = ""
    while True:
        subprocess.call('clear', shell=True)
        print "\n" + newplayer.getproperty('filename')
        cue_display = "Cue:"
        for x in range(len(playlist)):
            cue_display += "\n\t(" + str(x) + ") " + os.path.basename(playlist[x])
            if x > 4: 
                if len(playlist)>5:
                    cue_display += "\n\t..."
                break
        print cue_display

        if data:
            print "\n" + data
        if newplayer.paused == True:
            newplayer.pause()
            print "\n\n----paused----\n"
        command = raw_input("\n\t-->")
        command = command.rstrip().translate(None,"\\")
        if command == 'debug':
            print newplayer.info
        if "http" in command:
            playlist.append(command)
        if os.path.isfile(command):
            try:
                if mimetypes.guess_type(command)[0].partition('/')[0] in ('audio', 'video'):
                    playlist.append(command)
            except AttributeError:
                print "Not a valid file type"
        elif os.path.isdir(command):
            for fname in dirsearch.search(command):
                fname = fname.rstrip().translate(None,"\\")
                try:
                    if mimetypes.guess_type(fname)[0].partition('/')[0] in ('audio', 'video'):
                        playlist.append(os.path.join(command,fname))
                except AttributeError: pass
        elif command == 'next':
            if playlist != []:
                newplayer.stop()
                newplayer.playSong(playlist[0])
                playlist = playlist[1:]
        elif command in ('pause', 'play'):
            exec("newplayer." + command+"()")
        elif command.split()[0] in commands.keys():
            args = []
            if len(command.split())>1:
                args = command.split()[1:]
            data =  newplayer.command(command.split()[0], args)
        elif command.split()[0] == 'jump':
            number = int(command.split()[1])
            newplayer.stop()
            newplayer.playSong(playlist[number])
            playlist = playlist[number:]
        elif command == 'quit':
            newplayer.stop()
            break
