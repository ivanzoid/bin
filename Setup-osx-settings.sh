#!/bin/bash

## Safari
# Enable Develop Menu and Web Inspector
defaults write com.apple.Safari IncludeDevelopMenu -bool true
# Enable 'Never use font sizes smaller than:'
defaults write com.apple.Safari com.apple.Safari.ContentPageGroupIdentifier.WebKit2MinimumFontSize -int 14


# TODO:
# - Set download folder
# - Show statusbar
# - Show full site url


## TextEdit
# Use Plain Text Mode as Default
defaults write com.apple.TextEdit RichText -int 0

# TODO:
# Default font size


## Dock
# Position on screen: Left
defaults write com.apple.dock orientation -string left
# Add a Stack with Recent Applications
defaults write com.apple.dock persistent-others -array-add '{ "tile-data" = { "list-type" = 1; }; "tile-type" = "recents-tile"; }'

# TODO:
# - Minimize windows using: `Scale effect`
# - Minimize windows into application icon



## Mission control

# Turn on dashboard-as-space
defaults write com.apple.dashboard enabled-state 2
# TODO:
# - Mission control / Application windows: remove shortcuts
# - Show Desktop: set to Option-F11
# - Show Dashboard: set to Option-F12


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
# Expand Print Panel by Default
defaults write -g PMPrintingExpandedStateForPrint -bool true
# Show Status Bar
defaults write com.apple.finder ShowStatusBar -bool true
# Save to Disk by Default
defaults write -g NSDocumentSaveNewDocumentsToCloud -bool false
# Set Current Folder as Default Search Scope
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
# Disable Creation of Metadata Files on Network Volumes
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
# Disable Creation of Metadata Files on USB Volumes
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
# Set default view style to List
defaults write com.apple.Finder FXPreferredViewStyle clmv
# Set default Finder location to Desktop folder (~/Desktop)
defaults write com.apple.finder NewWindowTarget -string "PfLo" && \
defaults write com.apple.finder NewWindowTargetPath -string "file://${HOME}/Desktop"
# Disable ext change warning
defaults write com.apple.finder FXEnableExtensionChangeWarning -bool false
# Disable disk image verification
defaults write com.apple.frameworks.diskimages skip-verify -bool true && \
defaults write com.apple.frameworks.diskimages skip-verify-locked -bool true && \
defaults write com.apple.frameworks.diskimages skip-verify-remote -bool true
#Store screenshots in subfolder on desktop
mkdir ~/Desktop/Screenshots
defaults write com.apple.screencapture location ~/Desktop/Screenshots

# TODO:
# - Add 'Open with Terminal' to right-click menu



### Input Devices

## Keyboard

# Disable auto-correct
defaults write -g NSAutomaticSpellingCorrectionEnabled -bool false

# Enable Tab in modal dialogs
defaults write NSGlobalDomain AppleKeyboardUIMode -int 3

# Disable the default "press and hold" behavior.
defaults write -g ApplePressAndHoldEnabled -bool false
defaults write -g ApplePressAndHoldEnabled -bool false

# Key Repeat Rate
defaults write -g KeyRepeat -int 1
defaults write -g InitialKeyRepeat -int 10

## Trackpad
# Enable tap to click (Trackpad)
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Tap with two fingers to emulate right click
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadRightClick -bool true


# Enable three finger drag
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadThreeFingerDrag -bool true



## Mouse
# Follow mouse when zoomed in
defaults write com.apple.universalaccess closeViewPanningMode -int 0



### Other
# Enable AirDrop over Ethernet and on unsupported Macs
defaults write com.apple.NetworkBrowser BrowseAllInterfaces -bool true

# Set system beep sound volume to 0
defaults write com.apple.systemsound com.apple.sound.beep.volume -float 0

# Sort Activity Monitor results by CPU usage
defaults write com.apple.ActivityMonitor SortColumn -string "CPUUsage"
defaults write com.apple.ActivityMonitor SortDirection -int 0



### Security

## Firewall

# Enable Firewall Service
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on


killall Safari
killall Finder
killall Dock
killall SystemUIServer

