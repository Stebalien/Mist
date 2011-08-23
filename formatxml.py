#!/usr/bin/python

import sys

def format_xml(xml_file):
    f = ""
    for line in open(xml_file).readlines():
        f += line.strip()
    i = 0
    tabcount = -1
    direction = 1
    while i < len(f):
        if f[i] =='<':
            part1 = f[:i]
            part2 = f[i:]
            if f[i+1] == '/':
                if direction == 1:
                    insert = ''
                else:
                    tabcount -= 1
                    insert = "\n" + "\t" * tabcount
                direction = -1
            else:
                if direction == -1:
                    insert = "\n" + "\t" * tabcount
                else:
                    tabcount += 1
                    insert = "\n" + "\t" * tabcount
                direction = 1
            f = part1 + insert + part2
            i += len(insert)
        i += 1
    f = f.lstrip()
    open(xml_file, 'w').write(f)
    return f
if __name__ == '__main__':

    if len(sys.argv) == 2:
        args = sys.argv
        xml_file = args[1]
        format_xml(xml_file)

    else:
        print """
Usage: Formats xml file with proper newlines and tabs
Syntax: python formatxml.py [xml file]
"""
