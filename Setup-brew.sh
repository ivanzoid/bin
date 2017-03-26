#!/bin/bash

echo 'bash-completion
cuetools
exiftool
ffmpeg
flac
ghostscript
git
gnuplot
gpsbabel
htop-osx
hub
imagemagick
jbig2dec
jhead
jq
libvo-aacenc
macvim
ivanzoid/tap/merge-xcodeproj
midnight-commander
mmv
mplayer
mtr
mupdf-tools
poppler
python
rmtrash
ruby
shntool
uncrustify
unrar
ivanzoid/tap/viper-module-rename
wget
alexgarbarev/core/xc-resave' \
	| xargs brew install

brew tap caskroom/fonts
brew cask install font-go-mono

hardlink /usr/local/opt/macvim/MacVim.app /Applications/MacVim.app
