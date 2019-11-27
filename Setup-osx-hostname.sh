#!/bin/bash -x

sudo scutil --set ComputerName $@
sudo scutil --set HostName $@
sudo scutil --set LocalHostName $@
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string $@

