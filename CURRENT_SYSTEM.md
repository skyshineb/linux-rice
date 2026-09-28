# Current Linux desktop baseline

Captured on **2026-09-28** (Asia/Novosibirsk, UTC+07:00).

Versions below are installed Ubuntu package versions unless another source is named. Package versions include Debian epochs where present.

## Operating system and session

| Component | Current value | Source |
| --- | --- | --- |
| Distribution | Ubuntu 24.04.5 LTS | `/etc/os-release` |
| Kernel | Linux 7.0.0-34-generic, x86_64 | `uname` |
| Desktop session | KDE on X11 | `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE` |
| Graphics hardware | Intel UHD Graphics 620 | `lspci` |

## Desktop components and versions

| Component | Installed package version |
| --- | --- |
| KDE Plasma desktop (`plasma-desktop`) | `4:5.27.12-0ubuntu0.1` |
| KDE Plasma workspace, panel, and launcher (`plasma-workspace`) | `4:5.27.12-0ubuntu0.1` |
| KWin X11 window manager and compositor (`kwin-x11`) | `4:5.27.11-0ubuntu3` |
| Xorg server (`xserver-xorg-core`) | `2:21.1.12-1ubuntu1.8` |
| SDDM display manager (`sddm`) | `0.20.0-2ubuntu4.2` |
| Zsh shell (`zsh`) | `5.9-6ubuntu2` |
| Konsole terminal (`konsole`) | `4:23.08.5-0ubuntu4` |
| Dolphin file manager (`dolphin`) | `4:23.08.5-0ubuntu4` |
| Breeze theme (`breeze`) | `4:5.27.12-0ubuntu0.1` |
| Breeze icon theme (`breeze-icon-theme`) | `4:5.115.0-0ubuntu3` |
| Noto core fonts (`fonts-noto-core`) | `20201225-2` |
| Mesa Vulkan drivers (`mesa-vulkan-drivers:amd64`) | `25.2.8-0ubuntu0.24.04.2` |

SDDM is selected as the display manager in `/etc/X11/default-display-manager`. Konsole is selected by `/etc/alternatives/x-terminal-emulator`.

## Configured appearance

| Setting | Current value | Source |
| --- | --- | --- |
| Plasma look and feel | Breeze Dark (`org.kde.breezedark.desktop`) | `kdeglobals` |
| Color scheme | `BreezeDark` | `kdeglobals` |
| Icon theme | `breeze-dark` | `kdeglobals` |
| Cursor theme | `breeze_cursors` | `kcminputrc` |
| Plasma style | `default` | `plasmarc` |
| GTK 3 theme | `Breeze` | `gtk-3.0/settings.ini` |
| GTK 3 font | Noto Sans, 10 pt | `gtk-3.0/settings.ini` |
| Default sans font | Noto Sans Regular | `fc-match sans` |
| Default monospace font | Noto Sans Mono Regular | `fc-match monospace` |

This is a starting snapshot for desktop customization; it does not include every installed package.
