#!/usr/bin/env python
# vim: ts=4 sw=4

import os
import sys

if len(sys.argv) < 2:
	print 'message required'
	exit(0)

message = ' '.join(sys.argv[1:])

cmd = 'svn commit -m "%s"' % (path, message)

print cmd

os.system(cmd)
