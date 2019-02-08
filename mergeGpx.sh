#!/bin/bash
# Append multiple gpx files easily
# Save this as merge_gpx.sh
# Use: for example, to merge all files that start with 'track_2013' in the current folder, do:
# merge_gpx.sh track_2013*.gpx

gpsbabel -i gpx $(echo $* | for GPX; do echo -n " -f \"$GPX\" "; done) -o gpx -F appended.gpx
