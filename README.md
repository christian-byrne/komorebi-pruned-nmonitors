Komorebi Fork

## Changes

- Memory leak fix
- Choose monitor with arg so you can run multiple instances for each monitor
  - Automatically create config for each monitor to save settings
- Muted audio streams automatically
- Removed all features not related to video wallpapers (except time/date, webview, and assets)
- Removed GUIs: settings/preferences, wallpapercreator, wallpaperselector
  - Replaced with CLI script
- Removed all desktopicon features, drag and drop, clipboard control, animations
- Removed assets, defaults
- Removed other stuff I forgot
- Improved peformance, replaced deprecated methods
- Added CLI script to select/add/change wallpapers instead of the default GUIs.
  - Favorites, recents history
  - Create new wallpapers
  - Automatically create thumbnails, configs
  - Live updating search results, search by keyword
  - Shuffle wallpapers, shuffle from search results
  - add current to favorites, remove current from favorites
  - mark current to a text file list "to-edit"
  - delete current wallpaper (folder, assets, item in history and favs)
  - rename current wallpaper
  - When naming or renaming, gets common keywords/tags in other wallpaper names to help you name it in a way similar to other wallpapers
  - Makes temporary backups before any mutations
  - CLI Requires root on linux because uses keyboard listener 

