#!/bin/sh

program_exists () {
	type "$1" &> /dev/null ;
}

if ! program_exists ffmpeg; then
	echo "Please install ffmpeg"
	exit 1
fi

if ! program_exists metaflac; then
	echo "Please install flac"
	exit 1
fi

if ! program_exists shnsplit; then
	echo "Install shntool"
	exit 1
fi

if ! program_exists cuetag; then
	echo "Install cuetag"
	exit 1
fi

if ! program_exists alac_from_flac; then
	echo "alac_from_flac not found. Make sure it is in PATH"
	exit 1
fi

echo "Converting ape+cue to flac files ..."
shnsplit -f *.cue -o flac -t '%n %t' *.ape

echo "Tagging files ..."
cuetag *.cue *.flac

echo "Converting to ALAC ..."
alac_from_flac *.flac

echo "Removing temporary files ..."
rm *.flac

