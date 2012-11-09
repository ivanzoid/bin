#!/bin/sh

DROPBOX=$HOME/Dropbox/Settings

ln -f -s $DROPBOX/com.apple.Terminal.plist $HOME/Library/Preferences
ln -f -s $DROPBOX/login.keychain $HOME/Library/Keychains

rm -rf $HOME/Library/Developer/Xcode/UserData/CodeSnippets
ln -F -s $DROPBOX/Xcode/CodeSnippets $HOME/Library/Developer/Xcode/UserData

