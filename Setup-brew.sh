#!/bin/bash -x

echo 'bash-completion
exiftool
ffmpeg
flac
git
gpsbabel
htop
httpie
imagemagick
jhead
jq
mackup
macvim
ivanzoid/tap/merge-xcodeproj
midnight-commander
mtr
poppler
python
rmtrash
ruby
wget' \
	| xargs brew install

brew tap homebrew/cask-fonts
brew cask install font-go-mono
brew cask install font-fira-code

#hardlink /usr/local/opt/macvim/MacVim.app /Applications/MacVim.app
