#!/bin/bash -x

echo 'bash-completion
curl
exiftool
ffmpeg
flac
git
go
gpsbabel
htop
httpie
imagemagick
jq
macvim
python
rmtrash
ruby
wget' \
	| xargs brew install

#brew tap homebrew/cask-fonts
#brew cask install font-go-mono
#brew cask install font-fira-code

#hardlink /usr/local/opt/macvim/MacVim.app /Applications/MacVim.app
