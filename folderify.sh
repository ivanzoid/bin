#!/bin/sh

for file in *-*.* ; do
    if [ -f "$file" ]; then
	name=${file%\.*};
	echo "$file -> $name";
	mkdir -p "$name";
	mv "$file" "$name";
    fi;
done
