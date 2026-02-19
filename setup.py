#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess

name = ''
email = ''

# User
while name == '':
    name = input("What's your name?\n").strip() # type: ignore

# Email
while email == '' or '@' not in email:
    email = input("What's your email?\n").strip() # type: ignore

def show_notification(text):
    os.system('osascript -e \'display notification "' +
              text + '" with title "Mac Setup"\' > /dev/null')

print("Hey %s, lets setup your new Mac!" % name)
print("You'll be asked for your password a few times during this process")
print("*************************************")

# Create a Private Key
if not os.path.isfile(os.path.expanduser("~") + '/.ssh/id_rsa.pub'):
    print("---> Creating your private key...\n")
    os.system('ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N "" -C "%s"' % email)

# Set computer name & git info
os.system('sudo scutil --set ComputerName "%s"' % name)
os.system('sudo scutil --set HostName "%s"' % name)
os.system('sudo scutil --set LocalHostName "%s"' % name.replace(' ', '-'))
os.system('sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string "%s"' % name)
os.system('git config --global user.name "%s"' % name)
os.system('git config --global user.email "%s"' % email)

# Install Brew
print("---> Installing Brew...\n")
os.system('touch ~/.bash_profile')
os.system('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
os.system('(echo; echo \'eval "$(/opt/homebrew/bin/brew shellenv)"\') >> /Users/gtfunes/.zprofile')
os.system('eval "$(/opt/homebrew/bin/brew shellenv)"')
os.system('brew update && brew upgrade && brew cleanup')

# Install languages and dev tools
print("---> Installing Git+NodeJS+Python+Ruby+JDK+React-Native...\n")
os.system('brew install git python python3 nvm rbenv')
os.system('nvm install --lts && nvm use --lts && nvm alias default stable')
os.system('rbenv install 3.4.8 && rbenv global 3.4.8')
os.system('rbenv init')
os.system('brew link --overwrite git python python3')
os.system('brew unlink python && brew link --overwrite python')
os.system('brew install watchman')
os.system('sudo softwareupdate --install-rosetta')
os.system('brew install openjdk@11')
os.system('sudo ln -sfn /usr/local/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk')
os.system('brew install git-flow git-lfs')
os.system('git lfs install')

# Install some useful dev stuff
print("---> Installing useful stuff...\n")
os.system('brew install graphicsmagick curl wget sqlite libpng libxml2 openssl duti git-extras')
os.system('brew install pkg-config cairo pixman pango libpng jpeg giflib librsvg')
os.system('brew install bat tldr tree')

# Install AI tools
print("---> Installing AI tools...\n")
os.system('brew install --cask chatgpt')
os.system('brew install --cask claude')
os.system('brew install --cask claude-code')

# Install Apps only available via MAS
print("---> Installing MAS apps...\n")
os.system('brew install mas')
os.system('mas install 937984704') # Install Amphetamine
os.system('mas install 1388020431') # Install DevCleaner for Xcode
os.system('mas install 1522267256') # Install Shareful

# Install Apps
print("---> Installing Quicklook helpers...\n")
os.system('brew install --cask quicklook-csv quicklook-json webpquicklook suspicious-package qlstephen qlprettypatch qlvideo')

print("---> Installing powerline fonts...\n")
os.system('git clone https://github.com/powerline/fonts.git --depth=1 && ./fonts/install.sh')

print("---> Installing essential apps...\n")
os.system('brew install --cask 1password 1password-cli iterm2 rectangle the-unarchiver alt-tab raycast')
os.system(
    'brew install --cask google-chrome github visual-studio-code daisydisk')
os.system(
    'brew install --cask slack vlc zoom')
os.system(
    'brew install --cask docker cyberduck imageoptim handbrake postman')
os.system('brew install --cask android-studio')
os.system('brew install android-platform-tools')
os.system('brew install xcodes aria2')

print ("---> Installing Cocoapods...\n")
show_notification("We need your password:")
os.system('sudo gem install cocoapods')

print ("---> Installing Fastlane...\n")
show_notification("We need your password:")
os.system('sudo gem install fastlane --verbose')

# Oh-My-ZSH
print("---> Installing Oh-My-Zsh...\n")
show_notification("We need your password")

# Adapted from https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh
os.system('umask g-w,o-w && git clone --depth=1 https://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh')

if os.system('test -f ~/.zshrc') != 0:
    os.system('cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc')

os.system('git clone git://github.com/zsh-users/zsh-autosuggestions ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions')
os.system('git clone git://github.com/zsh-users/zsh-syntax-highlighting ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting')
os.system('git clone git://github.com/valentinocossar/vscode ~/.oh-my-zsh/custom/plugins/vscode')

# If the user has the default .zshrc tune it a bit
if (subprocess.call(['bash', '-c', 'diff <(tail -n +6 ~/.zshrc) <(tail -n +6  ~/.oh-my-zsh/templates/zshrc.zsh-template) > /dev/null']) == 0):
    # Agnoster Theme
    os.system('sed -i -e \'s/robbyrussell/agnoster/g\' ~/.zshrc &> /dev/null')
    # Plugins
    os.system('sed -i -e \'s/plugins=(git)/plugins=(git brew vscode node npm docker zsh-autosuggestions zsh-syntax-highlighting colored-man-pages copyfile extract)/g\' ~/.zshrc &> /dev/null')
    # Don't show the user in the prompt
    os.system('echo "DEFAULT_USER=\`whoami\`" >> ~/.zshrc')
    os.system('echo "export NVM_DIR=\"$HOME/.nvm\" \n [ -s \"/opt/homebrew/opt/nvm/nvm.sh\" ] && \. \"/opt/homebrew/opt/nvm/nvm.sh\" # This loads nvm \n [ -s \"/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm\" ] && \. \"/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm\"  # This loads nvm bash_completion" >> ~/.zshrc')

# Remove the 'last login' message
os.system('touch ~/.hushlogin')

# Random OSX Settings
print("---> Tweaking OSX settings...\n")

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

print("---> Tweaking system animations...\n")
os.system('defaults write NSGlobalDomain NSWindowResizeTime -float 0.1')
os.system('defaults write com.apple.dock expose-animation-duration -float 0.15')
os.system('defaults write com.apple.dock autohide-delay -float 0')
os.system('defaults write com.apple.dock autohide-time-modifier -float 0.3')
os.system('defaults write NSGlobalDomain com.apple.springing.delay -float 0.5')
os.system('killall Dock')

# Set default apps
print("---> Setting default applications...\n")

# Make Google Chrome the default browser
os.system('open -a "Google Chrome" --args --make-default-browser')

# Make iTerm the default app for .command files
os.system('duti -s com.googlecode.iterm2 .command all')

# Make VSCode the default app for development related files
os.system('duti -s com.microsoft.VSCode .js all')
os.system('duti -s com.microsoft.VSCode .jsx all')
os.system('duti -s com.microsoft.VSCode .ts all')
os.system('duti -s com.microsoft.VSCode .tsx all')
os.system('duti -s com.microsoft.VSCode .json all')
os.system('duti -s com.microsoft.VSCode .sh all')
os.system('duti -s com.microsoft.VSCode .yml all')
os.system('duti -s com.microsoft.VSCode .py all')
os.system('duti -s com.microsoft.VSCode .xml all')
os.system('duti -s com.microsoft.VSCode .md all')

# Clean Up Brew
print("--->Cleaning up Brew...\n")
os.system('brew cleanup')

# Mute startup sound
print("---> Muting system startup sound...\n")
show_notification("We need your password")
os.system('sudo nvram SystemAudioVolume=%00')

# Change the default shell to zsh
print("---> Switching default shell to zsh...\n")
os.system('chsh -s /bin/zsh &> /dev/null')

# Install latest Xcode
print("---> Installing latest Xcode (this will take a while)...\n")
os.system('xcodes install --latest')
os.system('sudo xcode-select --switch /Applications/Xcode.app') # Select Xcode app to avoid issues running apps later

print("*************************************")
show_notification("All done!")
