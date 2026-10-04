#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Prerequisites: Xcode Command Line Tools (run `xcode-select --install` first)
#
#   python3 setup.py           → set up a new Mac (interactive)
#   python3 setup.py --check   → report how this Mac drifted from the setup; writes nothing, exit 1 on drift
#   python3 setup.py --fix     → apply the safe fixes, ask before JDK changes, print what to change by hand

import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections import namedtuple

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

def brew_install(names, cask=False):
    """Install one package per brew call: one disabled or missing package must not block the rest."""
    for name in names:
        run_args(["brew", "install", *(["--cask"] if cask else []), name])

# What the setup installs. --check/--fix compare a Mac against these same lists.
RUBY_VERSION = "3.4.11"
FORMULAE = {
    "languages": ["git", "python", "nvm", "rbenv"],
    "watchman": ["watchman"],
    "git": ["gh", "git-flow-next", "git-lfs"],
    "useful": ["graphicsmagick", "curl", "wget", "sqlite", "libpng", "libxml2", "openssl", "duti", "git-extras"],
    "graphics": ["pkgconf", "cairo", "pixman", "pango", "jpeg", "giflib", "librsvg"],
    "cli": ["bat", "tlrc", "tree", "pipx"],
    "mas": ["mas"],
    "xcode": ["xcodes", "aria2"],
}
CASKS = {
    "jdk": ["zulu@17"],
    "ai": ["chatgpt", "claude", "claude-code"],
    "quicklook": ["suspicious-package", "syntax-highlight", "quicklook-video"],
    "essentials": ["1password", "1password-cli", "iterm2", "rectangle", "the-unarchiver", "alt-tab", "raycast"],
    "browsing": ["google-chrome", "github", "visual-studio-code", "daisydisk"],
    "communication": ["slack", "vlc", "zoom"],
    "tools": ["docker-desktop", "cyberduck", "imageoptim", "handbrake-app", "postman"],
    "android": ["android-studio", "android-platform-tools"],
}
# Packages earlier versions of this setup installed, and what replaces them (None: dropped).
REPLACED = {
    "tldr": "tlrc",                   # disabled in Homebrew (unmaintained)
    "git-flow": "git-flow-next",      # repo archived
    "openjdk@11": "zulu@17",          # unmaintained; React Native needs JDK 17
    "quicklook-csv": None,            # Quick Look generators stopped working on macOS 15
    "quicklook-json": None,
    "webpquicklook": None,
    "qlstephen": None,
    "qlprettypatch": None,
}
# Changing the JDK switches every Java build on the Mac, so --fix asks first.
CONFIRM = {
    "zulu@17": "Install zulu@17? JAVA_HOME picks the newest JDK, so Java builds will switch to 17.",
    "openjdk@11": "Remove openjdk@11? Do this only after a Java build works on JDK 17.",
}
# Packages left out on purpose on this Mac, one per line (# comments allowed); --check won't report them missing.
SKIP_FILE = "~/.config/mac-setup/skip"
OMZ_URL = "https://github.com/ohmyzsh/ohmyzsh.git"
OMZ_PLUGINS = {
    "zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions",
    "zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting",
}
NVM_PREFIX = 'export NVM_DIR="$HOME/.nvm" && [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && . "/opt/homebrew/opt/nvm/nvm.sh"'
ZSHRC_BLOCK = (
    '\n# Keep PATH entries unique, so nested shells don\'t stack duplicates. Both names are\n'
    '# needed: with only `path`, zsh doesn\'t dedupe `export PATH=...` string assignments.\n'
    'typeset -U PATH path\n'
    '\n# Lazy-load NVM (defers ~300-700ms until first use)\n'
    'export NVM_DIR="$HOME/.nvm"\n'
    '\n'
    '# Put the newest installed Node on PATH without loading nvm, so child processes\n'
    '# (editor and agent hooks, non-interactive shells) find `node` before the lazy loader has run.\n'
    '_nvm_node_bins=($NVM_DIR/versions/node/v*/bin(N/nOn))\n'
    '(( ${#_nvm_node_bins} )) && export PATH="${_nvm_node_bins[1]}:$PATH"\n'
    'unset _nvm_node_bins\n'
    'nvm_lazy_load() {\n'
    '  [[ -n $_NVM_LAZY_LOADED ]] && return\n'
    '  _NVM_LAZY_LOADED=1\n'
    '  unset -f nvm node npm npx pnpm pnpx\n'
    '  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \\. "/opt/homebrew/opt/nvm/nvm.sh"\n'
    '  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \\. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"\n'
    '}\n'
    'nvm() { nvm_lazy_load; nvm "$@"; }\n'
    'node() { nvm_lazy_load; node "$@"; }\n'
    'npm() { nvm_lazy_load; npm "$@"; }\n'
    'npx() { nvm_lazy_load; npx "$@"; }\n'
    'pnpm() { nvm_lazy_load; pnpm "$@"; }\n'
    'pnpx() { nvm_lazy_load; pnpx "$@"; }\n'
    '\n'
    '# NVM auto .nvmrc loading: find .nvmrc with plain zsh (nvm\'s own finder only exists\n'
    '# after the lazy load), then load nvm only when a project asks for a version.\n'
    'autoload -U add-zsh-hook\n'
    'load-nvmrc() {\n'
    '  local dir=$PWD\n'
    '  while [[ $dir != / && ! -f $dir/.nvmrc ]]; do dir=${dir:h}; done\n'
    '  [[ -f $dir/.nvmrc ]] || return 0\n'
    '  nvm_lazy_load\n'
    '  local node_version="$(nvm version)"\n'
    '  local nvmrc_node_version=$(nvm version "$(cat "$dir/.nvmrc")")\n'
    '  if [ "$nvmrc_node_version" = "N/A" ]; then\n'
    '    nvm install\n'
    '  elif [ "$nvmrc_node_version" != "$node_version" ]; then\n'
    '    nvm use\n'
    '  fi\n'
    '}\n'
    'add-zsh-hook chpwd load-nvmrc\n'
    'load-nvmrc\n'
    '\n'
    'eval "$(rbenv init - --no-rehash zsh)"\n'
)
# Lines of ZSHRC_BLOCK that --check looks for in ~/.zshrc, and lines that mark the old block.
ZSHRC_MARKERS = {
    "typeset -U PATH path": "keeps PATH entries unique",
    "_nvm_node_bins=": "puts Node on PATH for hooks and non-interactive shells",
    "_NVM_LAZY_LOADED": "loads nvm once, and finds .nvmrc files without loading it",
}
ZSHRC_STALE = {
    "nvm_find_nvmrc": "old .nvmrc hook that never fires while nvm is lazy-loaded",
}

# ---- Doctor: compare this Mac with the lists above -------------------------

Finding = namedtuple("Finding", "kind subject detail drift fix")

def expected_formulae():
    return {name for names in FORMULAE.values() for name in names}

def expected_casks():
    return {name for names in CASKS.values() for name in names}

def installed_index(brew_json):
    """Index `brew info --json=v2 --installed`: every name a package answers to, plus Homebrew's flags."""
    index = {"formula": set(), "cask": set(), "canonical": {}, "flagged": []}
    for f in brew_json.get("formulae", []):
        oldnames = f.get("oldnames") or ([f["oldname"]] if f.get("oldname") else [])
        index["formula"].update([f["name"], *f.get("aliases", []), *oldnames])
        _note_installed(index, "formula", f["name"], f)
    for c in brew_json.get("casks", []):
        index["cask"].update([c["token"], *c.get("old_tokens", [])])
        _note_installed(index, "cask", c["token"], c)
    return index

def _note_installed(index, kind, name, info):
    index["canonical"][name] = kind
    if info.get("disabled"):
        index["flagged"].append((kind, name, "disabled", info.get("disable_reason")))
    elif info.get("deprecated"):
        index["flagged"].append((kind, name, "deprecated", info.get("deprecation_reason")))

def parse_skip(text):
    return {line.split("#", 1)[0].strip() for line in (text or "").splitlines()} - {""}

def _confirmed(name, action):
    def fix():
        prompt = CONFIRM.get(name)
        if prompt:
            try:
                answer = input(f"{prompt} [y/N] ")
            except EOFError:  # no terminal to ask in: take the safe default
                answer = ""
            if answer.strip().lower() != "y":
                print(f"     skipped {name}")
                return
        action()
    return fix

def _uninstall_replaced(name, kind):
    def action():
        run_args(["brew", "uninstall", *(["--cask"] if kind == "cask" else []), name])
        jdk_link = "/Library/Java/JavaVirtualMachines/openjdk-11.jdk"
        if name == "openjdk@11" and os.path.islink(jdk_link):
            run_args(["sudo", "rm", jdk_link])
    return action

def package_findings(want_formulae, want_casks, replaced, index, skip=frozenset()):
    findings = []
    for kind, wanted in (("formula", want_formulae), ("cask", want_casks)):
        for name in sorted(wanted - index[kind] - skip):
            action = lambda name=name, kind=kind: brew_install([name], cask=kind == "cask")
            findings.append(Finding("missing", name, f"{kind} not installed", True, _confirmed(name, action)))
    for name, kind in sorted(index["canonical"].items()):
        if name in replaced:
            new = replaced[name]
            detail = f"replaced by {new}" if new else "dropped, no replacement"
            findings.append(Finding("replaced", name, detail, True, _confirmed(name, _uninstall_replaced(name, kind))))
    for kind, name, status, reason in index["flagged"]:
        if name not in replaced:
            detail = f"{kind} {status} in Homebrew ({reason}); left alone"
            findings.append(Finding("flagged", name, detail, False, None))
    return findings

def zshrc_findings(text):
    findings = [Finding("zshrc", line, f"missing: {why}", True, None)
                for line, why in ZSHRC_MARKERS.items() if line not in text]
    findings += [Finding("zshrc", line, f"{line} still present: {why}", True, None)
                 for line, why in ZSHRC_STALE.items() if line in text]
    return findings

def nvm_alias_findings(alias_text):
    if alias_text and alias_text.strip() == "lts/*":
        return []
    current = alias_text.strip() if alias_text else "unset"
    return [Finding("nvm", "default alias", f"is {current}, setup uses lts/*", True,
                    lambda: run(f"{NVM_PREFIX} && nvm alias default 'lts/*'"))]

def ruby_findings(current):
    if current == RUBY_VERSION:
        return []
    return [Finding("ruby", "rbenv global", f"is {current or 'unset'}, setup installs {RUBY_VERSION}; to upgrade by hand: "
                    f"rbenv install {RUBY_VERSION} && rbenv global {RUBY_VERSION}, then reinstall cocoapods and fastlane",
                    False, None)]

def ssh_findings(key_names):
    if "id_ed25519" in key_names:
        return []
    found = ", ".join(key_names) or "none"
    return [Finding("ssh", "~/.ssh", f"no Ed25519 key (found: {found}); existing keys are never changed. "
                    "To add one: ssh-keygen -t ed25519 -C <email>, then upload the .pub key to GitHub", False, None)]

def omz_findings(origin):
    if not origin or "robbyrussell/oh-my-zsh" not in origin:
        return []
    omz_dir = os.path.expanduser("~/.oh-my-zsh")
    return [Finding("oh-my-zsh", "origin", f"{origin} moved to {OMZ_URL}", True,
                    lambda: run_args(["git", "-C", omz_dir, "remote", "set-url", "origin", OMZ_URL]))]

def plugin_findings(custom_vscode_dir):
    if not os.path.isdir(custom_vscode_dir):
        return []
    trash = os.path.expanduser(f"~/.Trash/omz-custom-vscode-{time.strftime('%Y%m%d%H%M%S')}")
    return [Finding("oh-my-zsh", "custom vscode plugin", "2018 copy shadows oh-my-zsh's built-in vscode plugin (--fix moves it to the Trash)",
                    True, lambda: shutil.move(custom_vscode_dir, trash))]

def startup_mute_findings(nvram_output):
    if nvram_output and nvram_output.split()[-1] == "%01":
        return []
    return [Finding("macos", "startup sound", "StartupMute is not set", True,
                    lambda: run("sudo nvram StartupMute=%01"))]

def _output(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None

def _read(path):
    try:
        with open(os.path.expanduser(path)) as f:
            return f.read()
    except OSError:
        return None

def gather_findings():
    brew_json = json.loads(_output(["brew", "info", "--json=v2", "--installed"]) or "{}")
    keys = sorted(os.path.basename(p) for p in glob.glob(os.path.expanduser("~/.ssh/id_*")) if not p.endswith(".pub"))
    return (
        package_findings(expected_formulae(), expected_casks(), REPLACED, installed_index(brew_json),
                         skip=parse_skip(_read(SKIP_FILE)))
        + zshrc_findings(_read("~/.zshrc") or "")
        + nvm_alias_findings(_read("~/.nvm/alias/default"))
        + ruby_findings(_output(["rbenv", "global"]))
        + omz_findings(_output(["git", "-C", os.path.expanduser("~/.oh-my-zsh"), "remote", "get-url", "origin"]))
        + plugin_findings(os.path.expanduser("~/.oh-my-zsh/custom/plugins/vscode"))
        + ssh_findings(keys)
        + startup_mute_findings(_output(["nvram", "StartupMute"]))
    )

def report(findings):
    for f in findings:
        print(f"{'DRIFT' if f.drift else 'info ':5}  {f.kind:9} {f.subject}: {f.detail}")
    drift = sum(f.drift for f in findings)
    print(f"\n{drift} drift finding(s), {len(findings) - drift} informational")
    if any(f.kind == "missing" for f in findings):
        print(f"Packages you leave out on purpose: list them in {SKIP_FILE}")

def doctor(fix=False):
    if not shutil.which("brew"):
        print("brew not found; run the full setup first")
        return 1
    findings = gather_findings()
    report(findings)
    if not fix:
        return 1 if any(f.drift for f in findings) else 0
    for f in findings:
        if f.fix:
            print(f"---> {f.kind} {f.subject}")
            f.fix()
    if any(f.kind == "zshrc" for f in findings):
        print("\n---> ~/.zshrc is yours, so it is not edited automatically. Replace its nvm/PATH section with:\n")
        print(ZSHRC_BLOCK)
    print("\n---> After fixes:\n")
    findings = gather_findings()
    report(findings)
    return 1 if any(f.drift for f in findings) else 0

# ---- Setup -------------------------------------------------------------------

def main():
    # User
    name = ""
    email = ""

    while name == "":
        name = input("What's your name?\n").strip()

    while email == "" or "@" not in email:
        email = input("What's your email?\n").strip()

    safe_name = shlex.quote(name)

    print(f"Hey {name}, lets setup your new Mac!")
    print("You'll be asked for your password a few times during this process")
    print("*************************************")

    # Create a private key, only when there is none yet (existing keys are never touched)
    existing_keys = [p for p in glob.glob(os.path.expanduser("~/.ssh/id_*")) if not p.endswith(".pub")]
    if not existing_keys:
        print("---> Creating your private key...\n")
        run_args(["ssh-keygen", "-t", "ed25519", "-f",
                  os.path.expanduser("~/.ssh/id_ed25519"), "-N", "", "-C", email])

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
    brew_install(FORMULAE["languages"])

    # Source NVM in a subshell for commands that need it
    run(f"{NVM_PREFIX} && nvm install --lts && nvm use --lts && nvm alias default 'lts/*'")

    run(f"rbenv install -s {RUBY_VERSION} && rbenv global {RUBY_VERSION}")
    run('eval "$(rbenv init - zsh)"')
    run("brew link --overwrite git python")
    run("brew unlink python && brew link --overwrite python")
    brew_install(FORMULAE["watchman"])
    run("sudo softwareupdate --install-rosetta --agree-to-license")
    brew_install(CASKS["jdk"], cask=True)
    brew_install(FORMULAE["git"])
    run("git lfs install")

    # Install some useful dev stuff
    print("---> Installing useful stuff...\n")
    brew_install(FORMULAE["useful"])
    brew_install(FORMULAE["graphics"])
    brew_install(FORMULAE["cli"])

    # Install AI tools
    print("---> Installing AI tools...\n")
    brew_install(CASKS["ai"], cask=True)

    # Install Apps only available via MAS
    print("---> Installing MAS apps...\n")
    brew_install(FORMULAE["mas"])
    run("mas install 937984704")   # Amphetamine
    run("mas install 1388020431")  # DevCleaner for Xcode
    run("mas install 1522267256")  # Shareful

    # Install Quicklook helpers
    print("---> Installing Quicklook helpers...\n")
    brew_install(CASKS["quicklook"], cask=True)

    # Install powerline fonts
    print("---> Installing powerline fonts...\n")
    fonts_dir = os.path.join(tempfile.gettempdir(), "powerline-fonts")
    if not os.path.isdir(fonts_dir):
        run_args(["git", "clone", "https://github.com/powerline/fonts.git", "--depth=1", fonts_dir])
    run(f"{shlex.quote(fonts_dir)}/install.sh")

    # Install essential apps
    print("---> Installing essential apps...\n")
    brew_install(CASKS["essentials"], cask=True)
    brew_install(CASKS["browsing"], cask=True)
    brew_install(CASKS["communication"], cask=True)
    brew_install(CASKS["tools"], cask=True)
    brew_install(CASKS["android"], cask=True)
    brew_install(FORMULAE["xcode"])

    # Install Cocoapods & Fastlane (no sudo needed with rbenv)
    print("---> Installing Cocoapods...\n")
    run('eval "$(rbenv init - zsh)" && gem install cocoapods')

    print("---> Installing Fastlane...\n")
    run('eval "$(rbenv init - zsh)" && gem install fastlane')

    # Oh-My-ZSH
    print("---> Installing Oh-My-Zsh...\n")
    omz_dir = os.path.expanduser("~/.oh-my-zsh")
    if not os.path.isdir(omz_dir):
        run(f"umask g-w,o-w && git clone --depth=1 {OMZ_URL} {shlex.quote(omz_dir)}")

    # Install custom plugins (skip if already cloned)
    for plugin_name, plugin_url in OMZ_PLUGINS.items():
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
            f.write(ZSHRC_BLOCK)

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
    run("sudo nvram StartupMute=%01")

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

if __name__ == "__main__":
    if sys.argv[1:] in (["--check"], ["--fix"]):
        sys.exit(doctor(fix=sys.argv[1] == "--fix"))
    if sys.argv[1:]:
        print("usage: python3 setup.py [--check | --fix]")
        sys.exit(64)
    main()
