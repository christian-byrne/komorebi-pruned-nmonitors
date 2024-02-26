Komorebi Fork
# Changes

### Performance

- Fixed the issue causing crashes/hangups at 100% core usage by changing signal listeners and adding error handling callback to Player object
- Performance improvements
  - Listen for end-of-stream signal instead of listening to progress change and running check if video ended every frame
  - Listen to playback error signal and log erros then release the object and create a new one
  - Switch to keyframe based seeking instead of frame based seeking
  - All initialization-type functions are called conditionally only if they are necessary
  - Release objects that aren't used during background window instantiation
- Muted audio streams automatically
- Updated deprecated functions

### Multiple Monitors Solution

- The progrem accepts a monitor # argument when it's run, so you can create an instance for each monitor
- Automatically create config for each monitor to save settings

### Pruning

- Removed all features not related to video wallpapers (except time/date, webview, and assets)
- Removed GUIs: settings/preferences, wallpapercreator, wallpaperselector
  - Replaced with CLI script
- Removed all desktopicon features, drag and drop, clipboard control, animations
- Removed assets, defaults
- Removed other stuff I forgot

### Switch to CLI Interface

- Added CLI script to select/add/change wallpapers instead of the default GUIs.
- Features:
  - Built assuming you have multiple monitors and manages settings/configs for each one (and each instance of the program)
  - Favorites
  - Recents
  - Create new wallpapers
  - Automatically create thumbnails, configs
  - Live updating search results, search by keyword
  - Shuffle wallpapers, shuffle from search results
  - Add current to favorites, remove current from favorites
  - Mark current to a text file list "to-edit"
  - Delete current wallpaper (folder, assets, item in history and favs)
  - Rename current wallpaper
  - When naming or renaming, gets common keywords/tags in other wallpaper names to help you name it in a way similar to other wallpapers
  - Makes temporary backups before any mutations
- Requires root on linux because uses keyboard listener 
