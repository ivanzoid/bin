#!/usr/bin/env python

import sys
import sgmllib
import urllib
import urllib2
from urlparse import urlparse

def uniq(list):
    list.sort()
    last = list[-1]
    for i in range(len(list)-2, -1, -1):
        if last == list[i]:
            del list[i]
        else:
            last = list[i]

class Parser(sgmllib.SGMLParser):
    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
	self.links = {}

    def start_a(self, attrs):
        for name,value in attrs:
            if name.lower() == 'href':
		self.link = value

    def end_a(self):
	self.links[self.link] = self.data

    def handle_data(self, data):
	self.data = data

def get_link(host, link, name):
    ulink = urllib.unquote(link)
    extension = ulink[ulink.rfind('.'):]
    fname = name + extension
    fname = fname.decode('cp1251', 'replace')
    fname = fname.encode('utf-8', 'replace')
    full_link = link
    if not link.startswith('http'):
	full_link = host + '/' + link
    print('getting %s -> %s ...' % (full_link, fname))
    sock = urllib2.urlopen(full_link)
    out = open(fname,'wb')
    out.write(sock.read())
    out.close()

def get_files(url):
    sock = urllib2.urlopen(url)

    if not sock.info().dict['content-type'].startswith('text/html'):
	print('oops')
	exit()

    parser = Parser()
    parser.feed(sock.read())

    #uniq(parser.links)

    #for link in links:
    #    print link

    urlinfo = urlparse(url)
    host = urlinfo.scheme + '://' + urlinfo.netloc

    for link,name in parser.links.iteritems():
	try:
	    get_link(host, link, name)
	except:
	    print("Error processing %s" % link)


if len(sys.argv) == 2:
    url = sys.argv[1]
    get_files(url)
