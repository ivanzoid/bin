RD=Ramdisk
if [ ! -e "/Volumes/$RD" ];  then
	diskutil erasevolume HFS+ "$RD" `hdiutil attach -nomount ram://$((5000*2048))`
fi
