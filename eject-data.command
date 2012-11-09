#!/bin/sh

DISK=/dev/disk1s2

if ! mount | grep -q $DISK; then
	diskutil mountDisk $DISK
	sleep 2
fi

diskutil eject $DISK
