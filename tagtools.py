#!/usr/bin/python

import mimetypes
import sys
import types


class Tag:
    def __init__(self, filename, user_id=None):
       self.filename = filename 
       self.user_id = user_id
       self.file_type = mimetypes.guess_type(filename)[0]

    def read(self, details=[], ignore=[], force=False):
        data = {}
        details = [x.upper() for x in details]
        if force:
            for item in details:
                data[item] = ""
        return data, details

    def write(self, data):
        pass
    
    def trunc_list(self, data):
        if type(data) is types.ListType:
            return str(data[0])
        return str(data)
    
import mp3 as formats_mp3
import generic as formats_generic

mimetypes.add_type('audio/mp4', '.m4a')

def tag_handler(filename, user_id=None):
    file_type = mimetypes.guess_type(filename)[0]
    if file_type == 'audio/mpeg':
        return formats_mp3.Tag(filename,user_id)
    elif file_type in ('audio/ogg','audio/flac','audio/mp4'):
        return formats_generic.Tag(filename,user_id)
    else: 
        return Tag(None)


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        arguments = sys.argv[1:]
        data = {}
        details = []
        user_id = None
        while arguments:
            if arguments[0] == '-user':
                user_id = int(arguments[1])
                arguments = arguments[1:]
            elif arguments[0][0] == '+' and len(arguments)>1:
                data[arguments[0][1:]] = arguments[1]
                arguments = arguments[1:]
            elif arguments[0][0] == '-':
                details.append(arguments[0][1:])
            arguments = arguments[1:]
        tag_object = tag_handler(filename, user_id)
        failed_writes = tag_object.write(data)
        metadata,failed_reads = tag_object.read(details)
        print "\n-----Metadata----\n"  
        for x in sorted(metadata.keys()):
            print x, ":", metadata[x]
        print "\n\n"
        if failed_writes: print "Failed Writes: {0}".format(failed_writes)
        if failed_reads: print "\n\nFailed Reads: {0}".format(failed_reads)
            
    else:
        print """
Usage: Prints song metadata
Syntax: python editmetadata.py song file [-user user_id] u[+tag_name value] [-tag_name]
"""
