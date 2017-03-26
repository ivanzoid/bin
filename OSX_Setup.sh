#!/bin/bash

## Safari
# Enable Develop Menu and Web Inspector
defaults write com.apple.Safari IncludeDevelopMenu -bool true


## TextEdit
# Use Plain Text Mode as Default
defaults write com.apple.TextEdit RichText -int 0


## Dock
# Add a Stack with Recent Applications
defaults write com.apple.dock persistent-others -array-add '{ "tile-data" = { "list-type" = 1; }; "tile-type" = "recents-tile"; }' && \
killall Dock


## Finder

# Show All File Extensions
defaults write -g AppleShowAllExtensions -bool true
# Show Hidden Files
defaults write com.apple.finder AppleShowAllFiles true
# Show Full Path in Finder Title
defaults write com.apple.finder _FXShowPosixPathInTitle -bool true
# Unhide User Library Folder
chflags nohidden ~/Library
# Increase Number of Recent Places
defaults write -g NSNavRecentPlacesLimit -int 10
# Show "Quit Finder" Menu Item
defaults write com.apple.finder QuitMenuItem -bool true
# Expand Save Panel by Default
defaults write -g NSNavPanelExpandedStateForSaveMode -bool true
defaults write -g NSNavPanelExpandedStateForSaveMode2 -bool true
# Status Bar
defaults write com.apple.finder ShowStatusBar -bool true
# Save to Disk by Default
defaults write -g NSDocumentSaveNewDocumentsToCloud -bool false
# Set Current Folder as Default Search Scope
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
# Disable Creation of Metadata Files on Network Volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
# Disable Creation of Metadata Files on USB Volumes
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

killall Finder


### Input Devices

## Keyboard

# Disable auto-correct
defaults write -g NSAutomaticSpellingCorrectionEnabled -bool false

# Enable Tab in modal dialogs
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Disable the default "press and hold" behavior.
defaults write -g ApplePressAndHoldEnabled -bool false

# Key Repeat Rate
defaults write -g KeyRepeat -int 0.02


### Security

## Firewall

# Enable Firewall Service
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on



