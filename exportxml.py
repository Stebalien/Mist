#! /usr/bin/python

__author__="jonathan"

import xml.etree.ElementTree as ElementTree

import formatxml

def create_xml(user_id):
        if os.path.exists(self.xml_file):
            os.remove(self.xml_file)
        library_info['userid'] = user_id
        write()

def load(xml_file):
        """Load the library XML file into memory."""
        library = ElementTree.ElementTree()
        library.parse(xml_file)
        info_tree = library.find("info")
        library_info = {}
        for info_item in info_tree.iter():
            if info_item.tag != 'info':
                library_info[info_item.tag] = info_item.text
        library_tracks = load_tracks(library,user_id)
        library_playlists = load_playlists(user_id)
        return library_info,library_tracks, library_playlists

def load_tracks(library):
        tracks = {}
        tracks_tree = library.find("tracks")
        for track_tree in tracks_tree.findall("track"):
            track_id = int(track_tree.get("id"))
            track_data = {}
            for data_item in track_tree.iter():
                if data_item.tag != 'track':
                    track_data[data_item.tag] = data_item.text
            tracks[track_id] = track_data
        return tracks

def load_playlists(library):
    playlists = {}
    playlists_tree = library.find("playlists")
    for playlist_tree in playlists_tree.findall("playlist"):
        playlist_id = int(playlist_tree.get("id"))
        playlist_info = {}
        playlist_tracks = set()
        info_tree = playlist_tree.find("info")
        content_tree = playlist_tree.find("tracks")
        for info_item in info_tree.iter():
            if info_item != 'info':
                playlist_info[info_item.tag] = info_item.text
        for content_item in content_tree.iter():
            if content_item.tag != 'tracks':
                playlist_tracks.add(content_item.text)
        playlists[playlist_id] = (playlist_info, playlist_tracks)
    return playlists

def write(info,tracks,playlists={}):
        """
        XML Format:
        <dict>
            <info>
                <date></date>
                <location></location>
            </info>
            <tracks>
                <track id="0">
                    <location></location>
                    <title>Come Around</title>
                    ...other track information
                </track>
            </tracks>
            <playlists>
                <playlist id="1">
                    <info>
                        <title></title>
                        ...other playlist information
                    </info>
                    <tracks>
                        <track></track>
                    </tracks>
                </playlist>
            </playlists>
        </dict>
        """
        info['date'] = str(time.time())
        library = ElementTree.Element("dict")
        library_info = ElementTree.SubElement(library, "info")
        library_tracks = ElementTree.SubElement(library, "tracks")
        library_playlists = ElementTree.SubElement(library, "playlists")
        for info_item in info.keys():
            ElementTree.SubElement(library_info, info_item).text = info[info_item]
        for track_id in tracks.keys():
            library_track = ElementTree.SubElement(library_tracks, "track", {"id": str(track_id)})
            for info_item in tracks[track_id].keys():
                ElementTree.SubElement(library_track, info_item).text = tracks[track_id][info_item]
        for playlist_id in playlists.keys():
            library_playlist = ElementTree.SubElement(library_playlists, "playlist", {"id": str(playlist_id)})
            library_playlist_info = ElementTree.SubElement(library_playlist, "info")
            Library_playlist_tracks = ElementTree.SubElement(library_playlist, "tracks")
            for info_item in playlists[playlist_id][0].keys():
                ElementTree.SubElement(library_playlist_info, info_item).text = playlists[playlist_id][0][info_item]
            for track_id in playlists[playlist_id][1]:
                ElementTree.SubElement(library_playlist_tracks, "track").text = str(track_id)
        library = ElementTree.ElementTree(library)
        xml_file = info['location']
        library.write(xml_file, encoding="UTF-8")
        formatxml.format_xml(xml_file)
    
