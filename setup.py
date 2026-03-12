#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Prerequisites: Xcode Command Line Tools (run `xcode-select --install` first)

import glob
import os
import shlex
import subprocess
import tempfile

def run(cmd, check=False, sudo=False):
    """Run a shell command with logging."""
    if sudo:
        cmd = f"sudo {cmd}"
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"WARNING: Command failed (exit {result.returncode}): {cmd}")
    return result.returncode

def run_args(args, check=False):
    """Run a command with an argument list (no shell injection risk)."""
    result = subprocess.run(args)
    if check and result.returncode != 0:
        print(f"WARNING: Command failed (exit {result.returncode}): {' '.join(args)}")
    return result.returncode

def show_notification(text):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{text}" with title "Mac Setup"'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# User
name = ""
email = ""

while name == "":
    name = input("What's your name?\n").strip()

while email == "" or "@" not in email:
    email = input("What's your email?\n").strip()

safe_name = shlex.quote(name)
safe_email = shlex.quote(email)

print(f"Hey {name}, lets setup your new Mac!")
print("You'll be asked for your password a few times during this process")
print("*************************************")

# Create a Private Key
ssh_pub = os.path.expanduser("~/.ssh/id_rsa.pub")
if not os.path.isfile(ssh_pub):
    print("---> Creating your private key...\n")
    run_args(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f",
              os.path.expanduser("~/.ssh/id_rsa"), "-N", "", "-C", email])

# Set computer name & git info
local_hostname = name.replace(" ", "-")
run(f"sudo scutil --set ComputerName {safe_name}")
run(f"sudo scutil --set HostName {safe_name}")
run(f"sudo scutil --set LocalHostName {shlex.quote(local_hostname)}")
run(f"sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.smb.server NetBIOSName -string {safe_name}")
run_args(["git", "config", "--global", "user.name", name])
run_args(["git", "config", "--global", "user.email", email])

# Install Brew
if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
    print("---> Installing Brew...\n")
    run('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

    zprofile = os.path.expanduser("~/.zprofile")
    brew_line = 'eval "$(/opt/homebrew/bin/brew shellenv)"'
    # Only append if not already present
    if not os.path.isfile(zprofile) or brew_line not in open(zprofile).read():
        with open(zprofile, "a") as f:
            f.write(f"\n{brew_line}\n")

    # Add pipx PATH (used by pipx for installed tools)
    pipx_line = 'export PATH="$PATH:$HOME/.local/bin"'
    if not os.path.isfile(zprofile) or pipx_line not in open(zprofile).read():
        with open(zprofile, "a") as f:
            f.write(f"\n{pipx_line}\n")

# Propagate brew env into this Python process
os.environ["HOMEBREW_PREFIX"] = "/opt/homebrew"
os.environ["HOMEBREW_CELLAR"] = "/opt/homebrew/Cellar"
os.environ["HOMEBREW_REPOSITORY"] = "/opt/homebrew"
os.environ["PATH"] = "/opt/homebrew/bin:/opt/homebrew/sbin:" + os.environ.get("PATH", "")

run("brew update && brew upgrade && brew cleanup")

# Install languages and dev tools
print("---> Installing Git+NodeJS+Python+Ruby+JDK+React-Native...\n")
run("brew install git python python3 nvm rbenv")

# Source NVM in a subshell for commands that need it
nvm_prefix = 'export NVM_DIR="$HOME/.nvm" && [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && . "/opt/homebrew/opt/nvm/nvm.sh"'
run(f'{nvm_prefix} && nvm install --lts && nvm use --lts && nvm alias default stable')

run("rbenv install -s 3.4.8 && rbenv global 3.4.8")
run('eval "$(rbenv init - zsh)"')
run("brew link --overwrite git python python3")
run("brew unlink python && brew link --overwrite python")
run("brew install watchman")
run("sudo softwareupdate --install-rosetta --agree-to-license")
run("brew install openjdk@11")
run("sudo ln -sfn $HOMEBREW_PREFIX/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk")
run("brew install git-flow git-lfs")
run("git lfs install")

# Install some useful dev stuff
print("---> Installing useful stuff...\n")
run("brew install graphicsmagick curl wget sqlite libpng libxml2 openssl duti git-extras")
run("brew install pkg-config cairo pixman pango libpng jpeg giflib librsvg")
run("brew install bat tldr tree pipx")

# Install AI tools
print("---> Installing AI tools...\n")
run("brew install --cask chatgpt")
run("brew install --cask claude")
run("brew install claude-code")

# Install Apps only available via MAS
print("---> Installing MAS apps...\n")
run("brew install mas")
run("mas install 937984704")   # Amphetamine
run("mas install 1388020431")  # DevCleaner for Xcode
run("mas install 1522267256")  # Shareful

# Install Quicklook helpers
print("---> Installing Quicklook helpers...\n")
run("brew install --cask quicklook-csv quicklook-json webpquicklook suspicious-package qlstephen qlprettypatch qlvideo")

# Install powerline fonts
print("---> Installing powerline fonts...\n")
fonts_dir = os.path.join(tempfile.gettempdir(), "powerline-fonts")
if not os.path.isdir(fonts_dir):
    run_args(["git", "clone", "https://github.com/powerline/fonts.git", "--depth=1", fonts_dir])
run(f"{shlex.quote(fonts_dir)}/install.sh")

# Install essential apps
print("---> Installing essential apps...\n")
run("brew install --cask 1password 1password-cli iterm2 rectangle the-unarchiver alt-tab raycast")
run("brew install --cask google-chrome github visual-studio-code daisydisk")
run("brew install --cask slack vlc zoom")
run("brew install --cask docker cyberduck imageoptim handbrake postman")
run("brew install --cask android-studio")
run("brew install android-platform-tools")
run("brew install xcodes aria2")

# Install Cocoapods & Fastlane (no sudo needed with rbenv)
print("---> Installing Cocoapods...\n")
run('eval "$(rbenv init - zsh)" && gem install cocoapods')

print("---> Installing Fastlane...\n")
run('eval "$(rbenv init - zsh)" && gem install fastlane')

# Oh-My-ZSH
print("---> Installing Oh-My-Zsh...\n")
omz_dir = os.path.expanduser("~/.oh-my-zsh")
if not os.path.isdir(omz_dir):
    run(f"umask g-w,o-w && git clone --depth=1 https://github.com/robbyrussell/oh-my-zsh.git {shlex.quote(omz_dir)}")

# Install custom plugins (skip if already cloned)
plugins = {
    "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions",
    "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting",
    "vscode": "https://github.com/valentinocossar/vscode",
}
for plugin_name, plugin_url in plugins.items():
    plugin_dir = os.path.join(omz_dir, "custom", "plugins", plugin_name)
    if not os.path.isdir(plugin_dir):
        run_args(["git", "clone", plugin_url, plugin_dir])

zshrc = os.path.expanduser("~/.zshrc")
template = os.path.join(omz_dir, "templates", "zshrc.zsh-template")

if not os.path.isfile(zshrc):
    run_args(["cp", template, zshrc])

# If the user has the default .zshrc, tune it
diff_check = subprocess.run(
    ["bash", "-c", f"diff <(tail -n +6 {shlex.quote(zshrc)}) <(tail -n +6 {shlex.quote(template)}) > /dev/null"],
    capture_output=True
)
if diff_check.returncode == 0:
    # Set Agnoster theme
    run(f"sed -i '' 's/robbyrussell/agnoster/g' {shlex.quote(zshrc)}")
    # Set plugins
    run(f"sed -i '' 's/plugins=(git)/plugins=(git brew vscode node npm docker zsh-autosuggestions zsh-syntax-highlighting colored-man-pages copyfile extract)/g' {shlex.quote(zshrc)}")
    # Fix history settings (replace bash-isms with zsh equivalents)
    run(f"sed -i '' 's/HISTSIZE=1000/HISTSIZE=500/g' {shlex.quote(zshrc)}")
    run(f"sed -i '' 's/SAVEHIST=1000/SAVEHIST=500/g' {shlex.quote(zshrc)}")
    # Add Docker completions fpath before source oh-my-zsh.sh (so compinit picks it up)
    run(f"sed -i '' 's|source \\$ZSH/oh-my-zsh.sh|# Docker completions fpath (before oh-my-zsh so compinit picks it up)\\nfpath=($HOME/.docker/completions $fpath)\\n\\nsource $ZSH/oh-my-zsh.sh|g' {shlex.quote(zshrc)}")
    # Append additional config
    with open(zshrc, "a") as f:
        f.write('\nDEFAULT_USER="$USER"\n')
        f.write('\nexport LANG=en_US.UTF-8\n')
        f.write(
            '\n# Lazy-load NVM (defers ~300-700ms until first use)\n'
            'export NVM_DIR="$HOME/.nvm"\n'
            'nvm_lazy_load() {\n'
            '  unset -f nvm node npm npx\n'
            '  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"\n'
            '  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \\. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"\n'
            '}\n'
            'nvm() { nvm_lazy_load; nvm "$@"; }\n'
            'node() { nvm_lazy_load; node "$@"; }\n'
            'npm() { nvm_lazy_load; npm "$@"; }\n'
            'npx() { nvm_lazy_load; npx "$@"; }\n'
            '\n'
            '# NVM auto .nvmrc loading (triggers lazy load on cd)\n'
            'autoload -U add-zsh-hook\n'
            'load-nvmrc() {\n'
            '  local nvmrc_path="$(nvm_find_nvmrc 2>/dev/null)"\n'
            '  if [ -n "$nvmrc_path" ]; then\n'
            '    nvm_lazy_load\n'
            '    local node_version="$(nvm version)"\n'
            '    local nvmrc_node_version=$(nvm version "$(cat "${nvmrc_path}")")\n'
            '    if [ "$nvmrc_node_version" = "N/A" ]; then\n'
            '      nvm install\n'
            '    elif [ "$nvmrc_node_version" != "$node_version" ]; then\n'
            '      nvm use\n'
            '    fi\n'
            '  fi\n'
            '}\n'
            'add-zsh-hook chpwd load-nvmrc\n'
            '\n'
            'eval "$(rbenv init - --no-rehash zsh)"\n'
        )

# Remove the 'last login' message
hushlogin = os.path.expanduser("~/.hushlogin")
if not os.path.isfile(hushlogin):
    open(hushlogin, "a").close()

# macOS Settings
print("---> Tweaking macOS settings...\n")
# Finder: show hidden files by default
run("defaults write com.apple.finder AppleShowAllFiles -bool true")
# Finder: show all filename extensions
run("defaults write NSGlobalDomain AppleShowAllExtensions -bool true")
# Finder: allow text selection in Quick Look
run("defaults write com.apple.finder QLEnableTextSelection -bool true")
# Check for software updates daily
run("defaults write com.apple.SoftwareUpdate ScheduleFrequency -int 1")
# Disable auto-correct
run("defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false")
# Require password immediately after sleep or screen saver begins
run("defaults write com.apple.screensaver askForPassword -int 1")
run("defaults write com.apple.screensaver askForPasswordDelay -int 0")
# Show the ~/Library folder
run("chflags nohidden ~/Library")
# Don't automatically rearrange Spaces based on most recent use
run("defaults write com.apple.dock mru-spaces -bool false")
# Prevent Time Machine from prompting to use new hard drives as backup volume
run("defaults write com.apple.TimeMachine DoNotOfferNewDisksForBackup -bool true")
# Disable two finger swipe to go back/forward in Google Chrome
run("defaults write com.google.Chrome AppleEnableSwipeNavigateWithScrolls -bool false")

print("---> Tweaking system animations...\n")
run("defaults write NSGlobalDomain NSWindowResizeTime -float 0.1")
run("defaults write com.apple.dock expose-animation-duration -float 0.15")
run("defaults write com.apple.dock autohide-delay -float 0")
run("defaults write com.apple.dock autohide-time-modifier -float 0.3")
run("defaults write NSGlobalDomain com.apple.springing.delay -float 0.5")
run("killall Dock")

# Set default apps
print("---> Setting default applications...\n")

# Make Google Chrome the default browser
run('open -a "Google Chrome" --args --make-default-browser')

# Make iTerm the default app for .command files
run("duti -s com.googlecode.iterm2 .command all")

# Make VSCode the default app for development related files
vscode_extensions = [".js", ".jsx", ".ts", ".tsx", ".json", ".sh", ".yml", ".py", ".xml", ".md"]
for ext in vscode_extensions:
    run(f"duti -s com.microsoft.VSCode {ext} all")

# Clean Up Brew
print("---> Cleaning up Brew...\n")
run("brew cleanup")

# Mute startup sound
print("---> Muting system startup sound...\n")
run("sudo nvram SystemAudioVolume=%00")

# Change the default shell to zsh
print("---> Switching default shell to zsh...\n")
run("chsh -s /bin/zsh")

# Install latest Xcode
print("---> Installing latest Xcode (this will take a while)...\n")
run("xcodes install --latest")

# Find the installed Xcode app (xcodes names it e.g. "Xcode-16.3.app")
xcode_apps = sorted(glob.glob("/Applications/Xcode*.app"), reverse=True)
if xcode_apps:
    run(f"sudo xcode-select --switch {shlex.quote(xcode_apps[0])}")
else:
    print("WARNING: Could not find Xcode.app in /Applications")

print("*************************************")
show_notification("All done!")
