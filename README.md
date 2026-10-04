## Prerequisites
Install Xcode Command Line Tools:
```shell
xcode-select --install
```

## Install
```shell
curl -fsSL https://raw.githubusercontent.com/gtfunes/mac-setup/master/setup.py -o /tmp/setup.py && python3 /tmp/setup.py
```

## Check or fix an existing Mac
```shell
python3 /tmp/setup.py --check   # report drift from this setup; changes nothing, exit 1 on drift
python3 /tmp/setup.py --fix     # apply the safe fixes, ask before JDK changes
```
- Reports missing packages, packages this setup has replaced (for example `tldr` → `tlrc`), installed packages Homebrew marks deprecated or disabled, the nvm default, the oh-my-zsh setup, the `~/.zshrc` lines this setup writes, the Ruby version, SSH key type and startup mute.
- `--fix` never edits `~/.zshrc` (it prints the block to paste) and never touches SSH keys.
- Packages you leave out on purpose: list them one per line in `~/.config/mac-setup/skip`.

## Tests
```shell
python3 -m unittest discover -s tests -v
```

## What it does
- Asks for your name and email (used for git config and computer name)
- Generates an Ed25519 SSH key
- Installs [Homebrew](https://brew.sh)
- Installs dev tools: Git, Python, NVM (Node.js LTS), rbenv (Ruby), Azul Zulu JDK 17, Watchman, Rosetta 2
- Installs CLI utilities: GitHub CLI (gh), bat, tlrc (tldr), tree, pipx, curl, wget, git-extras, git-flow-next, git-lfs
- Installs AI tools: ChatGPT, Claude, Claude Code
- Installs apps: 1Password, iTerm2, Rectangle, Raycast, Google Chrome, VS Code, Docker, Slack, Zoom, VLC, and more
- Installs Mac App Store apps via `mas`: Amphetamine, DevCleaner, Shareful
- Installs Quick Look extensions (source code, video, installer packages) and Powerline fonts
- Installs CocoaPods and Fastlane
- Sets up Oh My Zsh with Agnoster theme, plugins, and lazy-loaded NVM — the newest Node stays on `PATH` for non-interactive tools and hooks, `.nvmrc` files switch versions on `cd`, and `PATH` entries are kept unique
- Configures macOS preferences (Finder, Dock, animations, privacy)
- Sets default apps (Chrome as browser, VS Code for dev files)
- Installs the latest Xcode via `xcodes`
