## Prerequisites
Install Xcode Command Line Tools:
```shell
xcode-select --install
```

## Install
```shell
curl -fsSL https://raw.githubusercontent.com/gtfunes/mac-setup/master/setup.py -o /tmp/setup.py && python3 /tmp/setup.py
```

## What it does
- Asks for your name and email (used for git config and computer name)
- Generates an SSH key
- Installs [Homebrew](https://brew.sh)
- Installs dev tools: Git, Python, NVM (Node.js), rbenv (Ruby), OpenJDK 11, Watchman, Rosetta 2
- Installs CLI utilities: bat, tldr, tree, pipx, curl, wget, git-extras
- Installs AI tools: ChatGPT, Claude, Claude Code
- Installs apps: 1Password, iTerm2, Rectangle, Raycast, Google Chrome, VS Code, Docker, Slack, Zoom, VLC, and more
- Installs Mac App Store apps via `mas`: Amphetamine, DevCleaner, Shareful
- Installs QuickLook plugins and Powerline fonts
- Installs CocoaPods and Fastlane
- Sets up Oh My Zsh with Agnoster theme, plugins, and lazy-loaded NVM
- Configures macOS preferences (Finder, Dock, animations, privacy)
- Sets default apps (Chrome as browser, VS Code for dev files)
- Installs the latest Xcode via `xcodes`
