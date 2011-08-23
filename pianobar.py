#!/usr/bin/python

import subprocess
import sys 
import os 
import thread

class Pianobar:

    def __init__(self):
        self.pause = False
        self.player = False
        self.unknownFeedback = []
        self.stations = {}
        self.screen = None
        self.info = []
        
    def startPlayer(self):
        if self.player:
            self.player.terminate()
            self.player = False
        self.player = subprocess.Popen(["/opt/local/bin/pianobar"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.pause = False
        thread.start_new_thread(self.getFeedback, ())

    def login(self, username, password):
        self.username = username
        self.password = password
        self.player.stdin.write(self.username+"\n")
        self.player.stdin.write(self.password+"\n")
        #self.player.stdin.write("5\n")

    def control(self, key):
        self.player.stdin.write(key)

    def terminate(self):
        if self.player:
            self.player.terminate()
            self.player = False
        
    def getFeedback(self):
        self.info = []
        self.info.append(self.player.stdout.readline())
        while self.player:
            feed = self.player.stdout.readline()
            feed = feed[4:].rstrip("\n")
            if "Get stations" in feed:
                self.screen = 'stations'
                self.stations = {}
                while True:
                    tempstation = self.player.stdout.readline()
                    tempstation = tempstation[4:].rstrip("\n").translate(None,")").split()
                    try:
                        if tempstation[1] == 'Q':
                            self.stations[int(tempstation[0])] = " ".join(tempstation[3:])
                        else:
                            self.stations[int(tempstation[0])] = " ".join(tempstation[1:])
                    except ValueError:
                        break

if __name__ == '__main__':
    username = "JonnieB300@gmail.com"
    password = "YPfZB2TOg"
    newpianobar = Pianobar()
    newpianobar.startPlayer()
    newpianobar.login(username, password)
    while True:
        keyboard = raw_input("\t--> ")
        if keyboard == 'debug':
            for x in newpianobar.stations.keys():
                print x,":",newpianobar.stations[x]
            for x in newpianobar.unknownFeedback:
                print x
        if keyboard == 'quit':
            newpianobar.terminate()
            break
        if keyboard in ('n',):
            newpianobar.control(keyboard)
