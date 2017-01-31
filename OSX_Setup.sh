#!/bin/bash

defaults write com.apple.Safari IncludeDevelopMenu -bool true

defaults write com.apple.TextEdit RichText -int 0

defaults write com.apple.dock persistent-others -array-add '{ "tile-data" = { "list-type" = 1; }; "tile-type" = "recents-tile"; }' && \
killall Dock


defaults write -g AppleShowAllExtensions -bool true
defaults write com.apple.finder AppleShowAllFiles true
defaults write com.apple.finder _FXShowPosixPathInTitle -bool true
chflags nohidden ~/Library
defaults write -g NSNavRecentPlacesLimit -int 10 && \

defaults write -g NSDocumentSaveNewDocumentsToCloud -bool false
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true


killall Finder
