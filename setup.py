#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# -*- coding: utf-8 -*-

import os
import json
import urllib2
import subprocess

name = ''
email = ''

# Check for Xcode Command Line Tools
if os.system('xcode-select -p') != 0:
    print "Installing XCode Command Line Tools..."
    os.system('xcode-select --install')
    print "**************************************************************"
    print "  Install XCode Command Line Tools and run this script again  "
    print "**************************************************************"
    exit()

# User
while name == '':
    name = raw_input("What's your name?\n").strip()

# Email
while email == '' or '@' not in email:
    email = raw_input("What's your email?\n").strip()


def show_notification(text):
    os.system('osascript -e \'display notification "' +
              text + '" with title "Mac Setup"\' > /dev/null')


print "Hey %s, lets setup your new Mac!" % name
print "You'll be asked for your password a few times during this process"
print "*************************************"

# Create a Private Key
if not os.path.isfile(os.path.expanduser("~") + '/.ssh/id_rsa.pub'):
    print "Creating your private key..."
    os.system('ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "%s"' % email)

# Set computer name & git info
os.system('sudo scutil --set ComputerName "%s"' % name)
os.system('sudo scutil --set HostName "%s"' % name)
os.system('sudo scutil --set LocalHostName "%s"' % name.replace(' ', '-'))
os.system('sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string "%s"' % name)
os.system('git config --global user.name "%s"' % name)
os.system('git config --global user.email "%s"' % email)

# Install Brew & Brew Cask
print "Installing Brew & Brew Cask..."
os.system('touch ~/.bash_profile')
os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
os.system('brew tap caskroom/cask')
os.system('brew tap homebrew/services')
os.system('brew tap caskroom/versions')
os.system('brew tap caskroom/fonts')
os.system('brew tap 0xmachos/homebrew-mosl')
os.system('brew update && brew upgrade && brew cleanup && brew cask cleanup')

# Install Languages
print "Installing Git+NodeJS+Python+Ruby+JDK+React-Native..."
os.system('brew install git node python python3 ruby')
os.system('brew link --overwrite git node python python3 ruby')
os.system('brew unlink python && brew link --overwrite python')
os.system('brew install watchman')
os.system('brew tap AdoptOpenJDK/openjdk')
os.system('brew cask install adoptopenjdk8')
os.system('npm install -g react-native-cli')
os.system('brew install git-flow git-lfs')
os.system('git lfs install')

# Install some useful dev stuff
print "Installing useful stuff..."
os.system('brew install graphicsmagick curl wget sqlite libpng libxml2 openssl duti git-extras')
os.system('brew install bat tldr tree')

# Install Apps only available via MAS
print "Installing MAS apps..."
os.system('brew install mas')
os.system('mas signin --dialog "%s"' % email)  # We need to sign in first!
os.system('mas install 937984704')  # Install Amphetamine

# Install Apps
print "Installing Quicklook helpers..."
os.system('brew cask install qlcolorcode qlmarkdown quicklook-csv quicklook-json webpquicklook suspicious-package epubquicklook qlstephen qlprettypatch font-hack qlvideo')

print "Installing fonts..."
os.system('brew cask install font-dosis font-droid-sans-mono-for-powerline font-open-sans font-open-sans-condensed font-roboto font-roboto-mono font-roboto-condensed font-roboto-slab font-consolas-for-powerline font-dejavu-sans font-dejavu-sans-mono-for-powerline font-inconsolata font-inconsolata-for-powerline font-lato font-menlo-for-powerline font-meslo-lg font-meslo-for-powerline font-noto-sans font-noto-serif font-source-sans-pro font-source-serif-pro font-ubuntu font-pt-mono font-pt-sans font-pt-serif font-fira-mono font-fira-mono-for-powerline font-fira-code font-fira-sans font-source-code-pro')

print "Installing essential apps..."
os.system('brew cask install iterm2 istat-menus rectangle the-unarchiver karabiner-elements authy')
os.system(
    'brew cask install google-chrome github visual-studio-code qbittorrent daisydisk macdown')
os.system(
    'brew cask install spotify slack whatsapp notion vlc zoomus cleanmymac discord')
os.system(
    'brew cask install docker sequel-pro cyberduck imageoptim postman crossover')
os.system('brew cask install android-studio')
os.system('brew install android-platform-tools')

os.system('brew cask fetch qlimagesize')
print "Installing QLImageSize..."
show_notification("We need your password:")
os.system('brew cask install qlimagesize')

os.system('brew cask fetch java')
print "Installing Java..."
show_notification("We need your password:")
os.system('brew cask install java')

print "Installing Cocoapods..."
show_notification("We need your password:")
os.system('sudo gem install cocoapods')

print "Installing Fastlane..."
show_notification("We need your password:")
os.system('sudo gem install fastlane --verbose')

print "Running security audit..."
os.system('brew install mosl')
os.system('Lockdown fix')

# Oh-My-ZSH
print "Installing Oh-My-Zsh with Dracula theme..."
show_notification("We need your password")

# Adapted from https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh
if os.system('test -n "$ZSH"') != 0:
    os.system('export ZSH=~/.oh-my-zsh')

if os.system('test -n "$ZSH_CUSTOM"') != 0:
    os.system('export ZSH_CUSTOM=~/.oh-my-zsh/custom')

if os.system('test -d "$ZSH"') != 0:
    os.system(
        'umask g-w,o-w && git clone --depth=1 https://github.com/robbyrussell/oh-my-zsh.git $ZSH')

if os.system('test -f ~/.zshrc') != 0:
    os.system('cp $ZSH/templates/zshrc.zsh-template ~/.zshrc')

os.system('git clone git://github.com/zsh-users/zsh-autosuggestions $ZSH_CUSTOM/plugins/zsh-autosuggestions')
os.system('git clone git://github.com/zsh-users/zsh-syntax-highlighting $ZSH_CUSTOM/plugins/zsh-syntax-highlighting')

# If the user has the default .zshrc tune it a bit
if (subprocess.call(['bash', '-c', 'diff <(tail -n +6 ~/.zshrc) <(tail -n +6  ~/.oh-my-zsh/templates/zshrc.zsh-template) > /dev/null']) == 0):
    # Agnoster Theme
    os.system('sed -i -e \'s/robbyrussell/agnoster/g\' ~/.zshrc &> /dev/null')
    # Plugins
    os.system('sed -i -e \'s/plugins=(git)/plugins=(git brew sublime node npm docker zsh-autosuggestions zsh-syntax-highlighting colored-man-pages copydir copyfile extract)/g\' ~/.zshrc &> /dev/null')
    # Customizations
    os.system('echo "alias dog=\'bat\'" >> ~/.zshrc')
    # Don't show the user in the prompt
    os.system('echo "DEFAULT_USER=\`whoami\`" >> ~/.zshrc')
    os.system(
        'echo "export NVM_DIR=\"\$HOME/.nvm\"\n[ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" # This loads nvm" >> ~/.zshrc')

# Remove the 'last login' message
os.system('touch ~/.hushlogin')

print "Dracula theme will be downloaded to your Desktop, set it later from iTerm profile color settings!"
os.system('git clone https://github.com/dracula/iterm.git ~/Desktop/dracula-theme/')

# Random OSX Settings
print "Tweaking OSX settings..."

# Finder: show hidden files by default
os.system('defaults write com.apple.finder AppleShowAllFiles -bool true')
# Finder: show all filename extensions
os.system('defaults write NSGlobalDomain AppleShowAllExtensions -bool true')

# Finder: allow text selection in Quick Look
os.system('defaults write com.apple.finder QLEnableTextSelection -bool true')
# Check for software updates daily
os.system('defaults write com.apple.SoftwareUpdate ScheduleFrequency -int 1')

# Disable auto-correct
os.system(
    'defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false')

# Require password immediately after sleep or screen saver begins
os.system('defaults write com.apple.screensaver askForPassword -int 1')
os.system('defaults write com.apple.screensaver askForPasswordDelay -int 0')
# Show the ~/Library folder
os.system('chflags nohidden ~/Library')
# Don’t automatically rearrange Spaces based on most recent use
os.system('defaults write com.apple.dock mru-spaces -bool false')
# Prevent Time Machine from prompting to use new hard drives as backup volume
os.system(
    'defaults write com.apple.TimeMachine DoNotOfferNewDisksForBackup -bool true')

# Disable two finger swipe to go back/forward in Google Chrome
os.system(
    'defaults write com.google.Chrome AppleEnableSwipeNavigateWithScrolls -bool false')

print "Tweaking system animations..."
os.system('defaults write NSGlobalDomain NSWindowResizeTime -float 0.1')
os.system('defaults write com.apple.dock expose-animation-duration -float 0.15')
os.system('defaults write com.apple.dock autohide-delay -float 0')
os.system('defaults write com.apple.dock autohide-time-modifier -float 0.3')
os.system('defaults write NSGlobalDomain com.apple.springing.delay -float 0.5')
os.system('killall Dock')

print "Enabling automatic Brew updates & upgrades..."
os.system('brew tap domt4/autoupdate')
os.system('brew autoupdate --start --upgrade')

# Make Google Chrome the default browser
os.system('open -a "Google Chrome" --args --make-default-browser')

# Make iTerm the default app for .command files
os.system('duti -s com.googlecode.iterm2 .command all')

# Make VSCode the default app for development related files
os.system('duti -s com.microsoft.VSCode .js all')
os.system('duti -s com.microsoft.VSCode .ts all')
os.system('duti -s com.microsoft.VSCode .json all')
os.system('duti -s com.microsoft.VSCode .sh all')
os.system('duti -s com.microsoft.VSCode .yml all')
os.system('duti -s com.microsoft.VSCode .py all')
os.system('duti -s com.microsoft.VSCode .xml all')
os.system('duti -s com.microsoft.VSCode .md all')

# Open Spectacle (Needs to be enabled manually)
os.system('open -a "Spectacle"')

# Clean Up Brew
os.system('brew cleanup && brew cask cleanup')

# Mute startup sound
show_notification("We need your password")
os.system('sudo nvram SystemAudioVolume=%00')

print "*************************************"
show_notification("All done!")

# Change the shell to zsh
os.system('chsh -s /bin/zsh &> /dev/null')
