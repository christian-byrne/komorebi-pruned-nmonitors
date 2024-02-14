import shutil
import os
import keyboard
from random import choice
from time import sleep
from termcolor import colored
from pathlib import Path

class UI:
    def __init__(self):
        self.MONITOR_INDEX = input("Enter monitor index (0 for primary, 1 for secondary, etc.): ")
        self.__HOME_PATH = Path.home()
        self.__PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
        # For standard install
        # self.__KOMOREBI_APP_PATH = "/System/Applications/komorebi"
        self.__KOMOREBI_APP_PATH = os.path.join("/", "home", "c_byrne", "projects", "komorebi-pruned-nmonitors", "komorebi")
        self.__KOMOREBI_WALLPAPER_DIRS_PATH = "/System/Resources/Komorebi"
        self.__KOMOREBI_CONFIG_FILE_NAME = f".Komorebi{self.MONITOR_INDEX}.prop"
        self.__KOMOREBI_CONFIG_FILE_PATH = self.locate_config_file()
        self.__HISTORY_FILE_PATH = os.path.join(self.__PROJECT_DIR, "data", "lists", "history.txt")
        self.__MAX_RECENT_HISTORY = 25
        self.MOST_RECENT_WALLPAPER = ""
        self.__FAVORITES_FILE_PATH = os.path.join(self.__PROJECT_DIR, "data", "lists", "favorites.txt")
        self.wallpapers = os.listdir(self.__KOMOREBI_WALLPAPER_DIRS_PATH)
        self.cur_input = ""

        # Sync history file with most recent wallpaper used by last instance of Komorebi
        if not os.path.exists(self.__HISTORY_FILE_PATH):
            print(f"[WARNING] Could not find history file at {self.__HISTORY_FILE_PATH}. Creating new history file.")
            open(self.__HISTORY_FILE_PATH, "w").close()
        self.sync_history()

        # Read favorites file
        self.favorites = []
        if not os.path.exists(self.__FAVORITES_FILE_PATH):
            print(f"[WARNING] Could not find favorites file at {self.__FAVORITES_FILE_PATH}. Creating new favorites file.")
            open(self.__FAVORITES_FILE_PATH, "w").close()
        self.read_favorites()

        self.instructions = "\n".join([
            "Start typing to search for wallpapers",
            f"{colored('ENTER', 'blue'):<25}{'Select first item in results':<35}",
            f"{colored('TAB', 'blue'):<25}{'Select random item in result':<35}",
            f"{colored('UP', 'blue'):<25}{'Move up in results':<35}",
            f"{colored('DOWN', 'blue'):<25}{'Move down in results':<35}",
            "",
            f"{colored('recent', 'cyan'):<25}{'Show recently used':<35}",
            f"{colored('favorites', 'cyan'):<25}{'Show favorites':<35}",
            f"{colored('edit', 'magenta'):<25}{'Enter edit mode (editing current wallpaper)':<35}",
            "",
            "Pressing ENTER or TAB on an empty list selects from all",
            ""
        ])
        self.prompt_char = "> "
        self.shift_pressed = False
        self.ignore_keys = ["alt", "ctrl", "esc", "cmd", "left", "right", "caps lock", "page up", "page down", "home", "end", "insert", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19"]
        self.shift_variants = {
            "1": "!",
            "2": "@",
            "3": "#",
            "4": "$",
            "5": "%",
            "6": "^",
            "7": "&",
            "8": "*",
            "9": "(",
            "0": ")",
            "-": "_",
            "−": "_",
            "=": "+",
            "[": "{",
            "]": "}",
            "\\": "|",
            ";": ":",
            "'": "\"",
            ",": "<",
            ".": ">",
            "/": "?"
        }
        self.datetime = {
            "Visible": False,
            "Parallax": False,
            "MarginTop": 0,
            "MarginRight": 0,
            "MarginLeft": 0,
            "MarginBottom": 0,
            "RotationX": 0,
            "RotationY": 0,
            "RotationZ": 0,
            "Position": "center",
            "Alignment": "center",
            "AlwaysOnTop": True,
            "Color": "#dd22dd22dd22",
            "Alpha": 255,
            "ShadowColor": "#dd22dd22dd22",
            "ShadowAlpha": 255,
            "TimeFont": "Lato Light 30",
            "DateFont": "Lato Light 20"
        }
        
        # To allow for quick random selection - On init, the search results will be all wallpapers (although none will be shown)
        self.cur_results = self.wallpapers
        self.cur_result_index = 0

        self.print_prompt_and_cur_input()

    # ----------------------------

    def create_new_wallpaper(self):
        self.clear()
        print("What should the wallpaper be called?")
        print("ENTER nothing to default to the video file name")
        print(self.prompt_char, end="", flush=True)
        wp_name = self.input_shift_buffer("edit").strip()

        # Get path from user
        self.clear()
        print("Enter the path to the video file")
        video_file_path = self._input().replace("~", "/home/" + os.getlogin())
        while not os.path.isfile(video_file_path) or os.path.isdir(video_file_path):
            self.clear()
            print("File does not exist or is a directory. Try again:")
            video_file_path = self._input().replace("~", "/home/" + os.getlogin())
        # replace aliases with full path
        video_file_path = os.path.abspath(video_file_path)

        # Update wallpaper name with the video file path if the name was not specified
        if wp_name == "":
            wp_name = os.path.basename(self.video_file_path).split(".")[0]
        
        # Create the wallpaper folder    
        os.mkdir(f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wp_name}")

        # Generate the datetime config
        self.generate_datetime_config()

        # Create the new wallpaper folders's config file
        self.create_wp_config(wp_name, video_file_path)

        # copy the video file to the wp_folder
        shutil.copy(video_file_path, f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wp_name}")

        # convert to mp4 if necessary
        if video_file_path.split(".")[-1] != "mp4":
            os.system(f"ffmpeg -i '{video_file_path}' '{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wp_name}/{wp_name}.mp4'")

        # create thumbnail from 2 seconds into video using ffmpeg
        os.system(f"ffmpeg -i '{video_file_path}' -ss 00:00:02.000 -vframes 1 {self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wp_name}/wallpaper.jpg")

        # refresh with new wallpaper
        self.refresh_with_new(wp_name)

    def create_wp_config(self, wp_name, video_file_path):
        """
        Config File Template:

        [Info]
        WallpaperType=video
        VideoFileName=tame impala ~ feels like we only go backwards ﾉ slowed + reverb ﾉ - 18.mp4

        [DateTime]
        Visible=false
        Parallax=false
        MarginTop=0
        MarginRight=0
        MarginLeft=0
        MarginBottom=0
        RotationX=0
        RotationY=0
        RotationZ=0
        Position=center
        Alignment=center
        AlwaysOnTop=true
        Color=#dd22dd22dd22
        Alpha=255
        ShadowColor=#dd22dd22dd22
        ShadowAlpha=255
        TimeFont=Lato Light 30
        DateFont=Lato Light 20

        """

        # create file called config in the wp_folder
        config_file = open(f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wp_name}/config", "w")

        # write the config file based on the template, replacing the values with the user's choices
        config_file.write("[Info]\n")
        config_file.write(f"WallpaperType=video\n")
        config_file.write(f"VideoFileName={os.path.basename(video_file_path)}\n\n")
        config_file.write("[DateTime]\n")
        config_file.write(f"Visible={str(self.datetime['Visible']).lower()}\n")
        config_file.write(f"Parallax={str(self.datetime['Parallax']).lower()}\n")
        config_file.write(f"MarginTop={self.datetime['MarginTop']}\n")
        config_file.write(f"MarginRight={self.datetime['MarginRight']}\n")
        config_file.write(f"MarginLeft={self.datetime['MarginLeft']}\n")
        config_file.write(f"MarginBottom={self.datetime['MarginBottom']}\n")
        config_file.write(f"RotationX={self.datetime['RotationX']}\n")
        config_file.write(f"RotationY={self.datetime['RotationY']}\n")
        config_file.write(f"RotationZ={self.datetime['RotationZ']}\n")
        config_file.write(f"Position={self.datetime['Position']}\n")
        config_file.write(f"Alignment={self.datetime['Alignment']}\n")
        config_file.write(f"AlwaysOnTop={str(self.datetime['AlwaysOnTop']).lower()}\n")
        config_file.write(f"Color={self.datetime['Color']}\n")
        config_file.write(f"Alpha={self.datetime['Alpha']}\n")
        config_file.write(f"ShadowColor={self.datetime['ShadowColor']}\n")
        config_file.write(f"ShadowAlpha={self.datetime['ShadowAlpha']}\n")
        config_file.write(f"TimeFont={self.datetime['TimeFont']}\n")
        config_file.write(f"DateFont={self.datetime['DateFont']}\n")

        config_file.close()

    def _input(self):
        print(self.prompt_char, end="", flush=True) 
        ret = self.input_shift_buffer("edit")
        return ret
    
    def generate_datetime_config(self):
        self.clear()
        print("Show Date and Time? (y/n)")
        if self._input().lower() != "y":
            return False
        else:
            self.datetime["Visible"] = True

        self.clear()
        print("Parallax? (y/n)")
        if self._input().lower() == "y":
            self.datetime["Parallax"] = True
        
        self.clear()
        print("Margin Top? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["MarginTop"] = int(selection)

        self.clear()
        print("Margin Right? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["MarginRight"] = int(selection)

        self.clear()
        print("Margin Left? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["MarginLeft"] = int(selection)

        self.clear()
        print("Margin Bottom? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["MarginBottom"] = int(selection)

        self.clear()
        print("Rotation X? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["RotationX"] = int(selection)

        self.clear()
        print("Rotation Y? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["RotationY"] = int(selection)

        self.clear()
        print("Rotation Z? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["RotationZ"] = int(selection)

        self.clear()
        print("Position? (center, top, bottom, left, right)")
        print("ENTER to skip (select default)")
        selection = self._input()
        while selection.lower() not in ["center", "top", "bottom", "left", "right", ""]:
            self.clear()
            print("Invalid selection. Must be center, top, bottom, left, or right. Try again:")
            selection = self._input()
        if selection != "":
            self.datetime["Position"] = selection
        
        self.clear()
        print("Alignment? (center, left, right)") 
        print("ENTER to skip (select default)")
        selection = self._input()
        while selection.lower() not in ["center", "left", "right", ""]:
            self.clear()
            print("Invalid selection. Must be center, left, or right. Try again:")
            selection = self._input()
        if selection != "":
            self.datetime["Alignment"] = selection

        self.clear()
        print("Always on top? (y/n)")
        print("ENTER to skip (select default)")
        if self._input().lower() == "y":
            self.datetime["AlwaysOnTop"] = True

        self.clear()
        print("Color? (hex)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["Color"] = selection

        self.clear()
        print("Alpha? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["Alpha"] = int(selection)

        self.clear()
        print("Shadow Color? (hex)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["ShadowColor"] = selection

        self.clear()
        print("Shadow Alpha? (int)")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["ShadowAlpha"] = int(selection)

        self.clear()
        print("Time Font? (font name). Formatted like 'Lato Light 30'")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["TimeFont"] = selection    

        self.clear()
        print("Date Font? (font name). Formatted like 'Lato Light 30'")
        print("ENTER to skip (select default)")
        selection = self._input()
        if selection != "":
            self.datetime["DateFont"] = selection

        return    

    # ----------------------------

    def get_active_wallpaper(self):
        """Gets the name of the currently active wallpaper.
        
        Returns:
            str: The name of the currently active wallpaper. If no wallpaper is active, returns an empty string.
        """
        with open(self.__KOMOREBI_CONFIG_FILE_PATH, "r") as config_file:
            config_file_lines = config_file.readlines()
        for line in config_file_lines:
            if "WallpaperName=" in line:
                return line.split("=")[1].strip()
        return ""

    def locate_config_file(self):
        """Locates the Komorebi config file.
        
        Returns:
            str: The path to the Komorebi config file.
        """
        
        # Get system users
        users = []
        if os.name == "nt":
            # Windows
            import winreg
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            reg_key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList")
            for i in range(1024):
                try:
                    users.append(winreg.EnumKey(reg_key, i))
                except:
                    break
        else:
            # Linux
            users = [f.name for f in os.scandir("/home") if f.is_dir()]
        
        for user in users:
            if os.name == "nt":
                # Windows
                home_dir = os.path.join("C:\\", "Users", user)
            else:
                # Linux
                home_dir = os.path.join("/home", user)
            
            # Check for default location before declaring other possible locations
            default_location = os.path.join(home_dir, self.__KOMOREBI_CONFIG_FILE_NAME)
            if os.path.exists(default_location):
                return default_location
        
            other_possible_locations = [
                [home_dir, ".config", "Komorebi", self.__KOMOREBI_CONFIG_FILE_NAME],
                [home_dir, ".local", "share", "Komorebi", self.__KOMOREBI_CONFIG_FILE_NAME],
                [home_dir, ".Komorebi", self.__KOMOREBI_CONFIG_FILE_NAME],
                [home_dir, ".config", self.__KOMOREBI_CONFIG_FILE_NAME],
                ["/", self.__KOMOREBI_CONFIG_FILE_NAME],
            ]

            # Add Windows-specific locations
            if os.name == "nt":
                other_possible_locations += [
                    [home_dir, "AppData", "Local", "Komorebi", self.__KOMOREBI_CONFIG_FILE_NAME],
                    [home_dir, "AppData", "Roaming", "Komorebi", self.__KOMOREBI_CONFIG_FILE_NAME],
                    [home_dir, "AppData", "Local", self.__KOMOREBI_CONFIG_FILE_NAME],
                ]

            for location in other_possible_locations:
                if os.path.exists(os.path.join(*location)):
                    return os.path.join(*location)
                
        
        # No config found
        default_location = os.path.join(self.__HOME_PATH, self.__KOMOREBI_CONFIG_FILE_NAME)
        print(f"[WARNING] Could not find a Komorebi config file. Using default location {default_location}.")
        print(f"[WARNING] Make sure config file is named '.Komorebi$I.prop' where $I is the monitor index (e.g., '.Komorebi0")
        print(f"[WARNING] Note that this is the config for the application, not the config for a wallpaper (which is named 'config' and is located in each wallpaper folder)")
        return default_location

    def read_favorites(self):
        with open(self.__FAVORITES_FILE_PATH, "r") as favorites_file:
            favorites = favorites_file.readlines()
        
        # Ensure each line corresponds to a wallpaper that exists
        for favorite in favorites:
            favorite = favorite.strip("\n")
            if favorite not in self.wallpapers:
                print(f"[WARNING] Favorite '{favorite}' in favorites file {self.__FAVORITES_FILE_PATH} does not exist in {self.__KOMOREBI_WALLPAPER_DIRS_PATH}. Consider updating favorites file.")
            else:
                self.favorites.append(favorite)

    def sync_history(self):
        """Adds the most recent wallpaper used by the last instance of Komorebi to the history file.
        
        History file is located at ./data/history.
        """
        
        # Ensure that the Komorebi config file exists
        if not os.path.exists(self.__KOMOREBI_CONFIG_FILE_PATH):
            print(f"[WARNING] Could not find Komorebi config file at {self.__KOMOREBI_CONFIG_FILE_PATH}. Aborting history update.")
            # don't update history if config file doesn't exist because nothing to add
            return
        
        # Check the current wallpaper in the config file (most recent wallpaper used by the last instance of Komorebi)
        with open(self.__KOMOREBI_CONFIG_FILE_PATH, "r") as config_file:
            config_file_lines = config_file.readlines()
        wallpaper = ""
        for line in config_file_lines:
            if "WallpaperName=" in line:
                wallpaper = line.split("=")[1].strip()
                break

        # If somehow the wallpaper name can't be found, abort and don't update history
        if wallpaper == "":
            print(f"[WARNING] Could not parse the most recent wallpaper used by Komorebi from config file {self.__KOMOREBI_CONFIG_FILE_PATH}. Aborting history update.")
            return
        
        # If the current wallpaper is not already the most recent item in the history file, add it
        with open(self.__HISTORY_FILE_PATH, "r") as history_file:
            history_file_lines = history_file.readlines()
            # Get most recent non-empty line
            most_recent_line = ""
            while most_recent_line == "" or most_recent_line == "\n":
                # Ensure lines are not empty
                if len(history_file_lines) == 0:
                    break
                most_recent_line = history_file_lines.pop().strip("\n").strip()  

            if most_recent_line == "":
                print("[WARNING] History file is empty.")

        # Update most recent wallpaper variable
        if wallpaper in self.wallpapers:
            self.MOST_RECENT_WALLPAPER = wallpaper 

        # If (1) the most recent wallpaper is not already the most recent wallpaper in the history file, or
        #    (2) the most recent line in history is empty (i.e., the history file is empty), then 
        # add the wallpaper 
        if wallpaper != most_recent_line or most_recent_line == "":

            # Only add if wallpaper is in the list of wallpapers (in case the wallpaper has been deleted since last time running Komorebi)
            if wallpaper in self.wallpapers:
                with open(self.__HISTORY_FILE_PATH, "a") as history_file:
                    history_file.write(wallpaper + "\n")
            else:
                print(f"[WARNING] Attempted to update history but the most recent wallpaper used by Komorebi ('{wallpaper}') is no longer in {self.__KOMOREBI_WALLPAPER_DIRS_PATH}. It may have been deleted since last time running Komorebi.")

    def print_highlighted(self, text, color='red', on_color='on_black'):
        colored_text = colored(text, color, on_color)
        print(colored_text)

    def clear(self):
        os.system("clear")

    def get_shift_variant(self, key):
        # if a letter, return uppercase
        if key.isalpha():
            return key.upper()
        # if a number or symbol, return the shifted variant
        elif key in self.shift_variants:
            return self.shift_variants[key]
        # if not a letter, number, or symbol, return the key
        else:
            return key
        
    def set_wallpaper(self, wallpaper):
        config_file = open(self.__KOMOREBI_CONFIG_FILE_PATH, "r")
        config_file_lines = config_file.readlines()
        config_file.close()

        new_lines = []
        for line in config_file_lines:
            if "WallpaperName=" in line:
                new_lines.append(f"WallpaperName={wallpaper}\n")
            else:
                new_lines.append(line)

        config_file = open(self.__KOMOREBI_CONFIG_FILE_PATH, "w")
        for line in new_lines:
            config_file.write(line)    
        config_file.close()

    def get_cur_user(self):
        if os.name == "nt":
            return self.__PROJECT_DIR.split("\\")[2]
        else:
            return self.__PROJECT_DIR.split("/")[2]

    def update_results(self):
        self.clear()
        self.cur_results = []

        # If cur input is 'edit', exit normal mode and enter edit mode
        if self.cur_input.lower() == "edit":
            keyboard.unhook_all() 
            try:
                self.edit_mode()
            except KeyboardInterrupt:
                # Stop listening for key events
                exit("\nProgram stopped.")

            exit()

        # If current input is "recent", cur_results is history file items
        elif self.cur_input.lower() == "recent":
            print("Recent wallpapers:")
            with open(self.__HISTORY_FILE_PATH, "r") as history_file:
                history_file_lines = history_file.readlines()
                history_file_lines.reverse()

                for item in history_file_lines:
                    # Don't display more than the max number of recent items
                    if len(self.cur_results) >= self.__MAX_RECENT_HISTORY:
                        break
                    
                    # Don't add empty lines
                    if item.strip("\n") != "":
                        self.cur_results.append(item.strip("\n"))
                    

        # If current input is "favorites", cur_results is favorites file items
        elif self.cur_input.lower() == "favorites":
            print("Favorite wallpapers:")
            for item in self.favorites:
                self.cur_results.append(item)

        # If normal search, cur_results if search results
        else:
            for wallpaper in self.wallpapers:
                if self.cur_input.lower() in wallpaper.lower():
                    self.cur_results.append(wallpaper)
        
        self.print_results()
        print()
        self.print_prompt_and_cur_input()
    
    def print_results(self):
        # Ensure that the current result index is within the bounds of the current results
        if self.cur_result_index >= len(self.cur_results):
            self.cur_result_index = 0
        
        # If no results, print message
        if len(self.cur_results) == 0:
            print("No wallpaper folder found that starts with that input.")
            return
        
        # Segment the results into 3 parts (before, current selected line, after)
        if self.cur_result_index == 0:
            self.print_highlighted(self.cur_results[self.cur_result_index])
            print("\n".join(self.cur_results[self.cur_result_index + 1:]))
        else:
            print("\n".join(self.cur_results[:self.cur_result_index]))
            self.print_highlighted(self.cur_results[self.cur_result_index])
            if self.cur_result_index != len(self.cur_results) - 1:
                print("\n".join(self.cur_results[self.cur_result_index + 1:]))
    
    def refresh_with_new(self, wallpaper):
        print(f"[REFRESH] Setting wallpaper to '{colored(wallpaper, 'green')}' ...")
        print("[REFRESH] Killing any active Komorebi processes ...")
        self.kill_komorebi()
        print("[REFRESH] Updating Config")
        self.set_wallpaper(wallpaper)
        print("[REFRESH] Starting Komorebi ...")
        self.start_komorebi()
        self.update_results()

    def select_from_results(self, index):
        """Selects a wallpaper from the current results and sets it as the wallpaper.
        
        Args:
            index (int): The index of the wallpaper to select from the current results. If -1, a random wallpaper is selected.    
        
        Returns:
            str: The name of the selected wallpaper.
        """

        print(f"Selecting {'random' if index == -1 else 'highlighted'} wallpaper from current results ...")
        # Ensure that there are results to select from
        if len(self.cur_results) == 0:
            print("[ERROR] Results are empty, nothing to select from")
            print(f"[ERROR] If you want to select from all, delete all current input then {colored('TAB', 'blue') if index == -1 else colored('ENTER', 'blue')}")
            return False
    
        if index == -1:
            wallpaper = choice(self.cur_results)
        else:
            try:
                wallpaper = self.cur_results[index]
            except IndexError:
                print(f"[WARNING] Index {index} is out of bounds of current results.\n[WARNING] Selecting random wallpaper from current results ...")
                wallpaper = choice(self.cur_results)

        return wallpaper

    # ----------------------------

    def edit_mode(self):
        self.clear()
        self.print_highlighted("Edit mode")
        
        print("The 'Active Wallpaper' refers to the wallpaper that is currently being displayed by Komorebi")
        print("If Komorebi is not running, it will refer to the wallpaper that was last displayed by Komorebi\n")

        print("Active Wallpaper:")
        print(colored(self.get_active_wallpaper(), "green"))
        print()

        print(f"Enter {colored('rename', 'cyan')} to rename the Active Wallpaper")
        print(f"Enter {colored('fav', 'cyan')} to add the Active Wallpaper to favorites")
        print(f"Enter {colored('unfav', 'cyan')} to remove the Active Wallpaper from favorites")
        print(f"Enter {colored('delete', 'cyan')} to delete the Active Wallpaper")
        print(f"Enter {colored('pcurrent', 'cyan')} to print path to Active Wallpaper and add to system clipboard")
        print(f"Enter {colored('create-new', 'cyan')} to create a new wallpaper from a video file")
        print(f"Enter {colored('mark', 'cyan')} to add the Active Wallpaper to the to-edit.txt list (data/lists/to-edit.txt)")

        valid_inputs = ["rename", "fav", "unfav", "delete", "pcurrent", "create-new", "mark"]

        print(self.prompt_char, end="", flush=True)
        edit_input = self.input_shift_buffer("edit").lower()

        while edit_input not in valid_inputs:
            print(f"Invalid input '{edit_input}'")
            print(f"Valid inputs are: {', '.join(valid_inputs)}")
            print(self.prompt_char, end="", flush=True)
            edit_input = self.input_shift_buffer("edit").lower()

        if edit_input == "rename":
            self.rename_wallpaper(self.get_active_wallpaper())
        elif edit_input == "pcurrent":
            self.print_and_pipe_cur_wp_path()
        elif edit_input == "fav":
            self.add_to_favorites(self.get_active_wallpaper())
        elif edit_input == "unfav":
            self.remove_from_favorites(self.get_active_wallpaper())
        elif edit_input == "delete":
            self.delete_wallpaper(self.get_active_wallpaper())
        elif edit_input == "create-new":
            self.create_new_wallpaper()
        elif edit_input == "mark":
            self.queue_edit(self.get_active_wallpaper())

    def queue_edit(self, wallpaper):
        # Add to file if it's not already in there
        with open(os.path.join(self.__PROJECT_DIR, "data", "lists", "to-edit.txt"), "r") as to_edit_file:
            to_edit_file_lines = [line.strip("\n") for line in to_edit_file.readlines()]
            if wallpaper in to_edit_file_lines:
                print(f"[WARNING] Wallpaper '{wallpaper}' is already in to-edit.txt")
                print(f"[WARNING] Aborting add to to-edit.txt")
                return
            
        with open(os.path.join(self.__PROJECT_DIR, "data", "lists", "to-edit.txt"), "a") as to_edit_file:
            to_edit_file.write(wallpaper + "\n")

        print(f"Added '{colored(wallpaper, 'green')}' to to-edit.txt")
        exit()

    def delete_wallpaper(self, wallpaper):
        self.clear()
        print(f"Wallpaper: {colored(wallpaper, 'green')}")
        print("\nWARNING: This will delete the wallpaper folder and all its contents. This cannot be undone.")
        print("Delete the wallpaper listed above? (y/n)")

        print(self.prompt_char, end="", flush=True)
        delete_input = self.input_shift_buffer("edit").lower()

        if delete_input == "y":
            print("Are you sure you want to delete this wallpaper? (y/n)")
            confirmation_input = self.input_shift_buffer("edit").lower()
            if confirmation_input != "y":
                print("Aborting delete")
                return
            else:
                self.ask_for_backup(wallpaper)
                print(f"Deleting '{colored(wallpaper, 'green')}' ...")

                self.kill_komorebi()
                # If the wallpaper was in favorites, remove it from favorites and update favorites file
                if wallpaper in self.favorites:
                    self.remove_from_favorites(wallpaper)

                # Set new replacement wallpaper as random from favorites
                print("Setting replacement ...")
                print("Choosing random wallpaper from favorites ...")
                if len(self.favorites) == 0:
                    print("No favorites to choose from. Selecting random from all ...")
                    replacement = choice(self.wallpapers)
                else:
                    replacement = choice(self.favorites)
                print(f"Setting replacement to '{colored(replacement, 'green')}' ...")
                self.set_wallpaper(choice(self.favorites))

                # Delete the wallpaper folder
                shutil.rmtree(f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wallpaper}")
                print(f"Deleted '{colored(wallpaper, 'green')}'")

                self.start_komorebi()
                exit()
        else:
            print("Aborting delete")
            exit()

    def remove_from_favorites(self, wallpaper):
        if wallpaper not in self.favorites:
            print(f"[WARNING] Wallpaper '{wallpaper}' is not in favorites")
            print(f"[WARNING] Aborting remove from favorites")
            return
        
        with open(self.__FAVORITES_FILE_PATH, "w") as favorites_file:
            for favorite in self.favorites:
                if favorite != wallpaper:
                    favorites_file.write(favorite + "\n")
        
        self.favorites.remove(wallpaper)
        print(f"Removed '{colored(wallpaper, 'green')}' from favorites")
        exit()

    def add_to_favorites(self, wallpaper):
        if wallpaper in self.favorites:
            print(f"[WARNING] Wallpaper '{wallpaper}' is already in favorites")
            print(f"[WARNING] Aborting add to favorites")
            return
        
        with open(self.__FAVORITES_FILE_PATH, "a") as favorites_file:
            favorites_file.write(wallpaper + "\n")
        
        self.favorites.append(wallpaper)
        print(f"Added '{colored(wallpaper, 'green')}' to favorites")
        exit()

    def input_shift_buffer(self, buffer):
        ret = input()
        # use buffer as if it is a newline character in stdin
        if buffer != "" and buffer in ret:
            ret = ret.split(buffer)[-1]

        return ret

    def print_and_pipe_cur_wp_path(self):
        """
        Print the path to the active wallpaper and copy it to the system clipboard.

        This function determines the user based on the operating system and
        constructs the path to the active wallpaper. It then prints the path and
        attempts to copy it to the system clipboard using platform-specific
        commands (runas on Windows, sudo -u on Linux/Mac).

        Note:
        - The function checks for the availability of clipboard tools (clipboard,
          xclip, pbcopy) and uses the first available tool.
        - If no clipboard tool is found, it prompts the user to copy the path manually.

        Raises:
        - Exception: If there is an error while executing system commands.
        - Exception: If clipboard tools are not found on Linux/Mac.

        """

        user = self.get_cur_user()

        active_wallpaper_path = f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{self.get_active_wallpaper()}"
        print(f"Path to Active Wallpaper:\n{active_wallpaper_path}")

        try:
            if os.name == "nt":
                os.system(f'echo {active_wallpaper_path} | runas /user:{user} clip')
            else:
                clipboard_command = None

                if shutil.which('clipboard'):
                    clipboard_command = 'clipboard'
                elif shutil.which('xclip'):
                    clipboard_command = 'xclip -selection clipboard'
                elif shutil.which('pbcopy'):
                    clipboard_command = 'pbcopy'

                if clipboard_command:
                    os.system(f'echo {active_wallpaper_path} | sudo -u {user} {clipboard_command}')
                else:
                    print("[ERROR] Clipboard tool not found. Install one (xclip, clipboard, pbcopy on mac). Or copy the path manually from the terminal window.")
        except Exception as e:
            print(f"[ERROR] Could not add path to Active Wallpaper to the system clipboard: {e}")
            print("[ERROR] Try installing clipboard (Linux) or xclip (Linux) or pbcopy (Mac)")
            print("[ERROR] Otherwise, copy the path manually from the terminal window")

    def ask_for_backup(self, wallpaper):
        self.clear()
        print(f"Wallpaper: {colored(wallpaper, 'green')}")
        
        print("\nWallpaper is about to be modified")
        print("Would you like to create a backup of the wallpaper folder in the project directory? (y/n)")

        print(self.prompt_char, end="", flush=True)
        backup_input = self.input_shift_buffer("edit").lower()

        if backup_input == "y":
            success = self.backup_wallpaper_folder(wallpaper)
            if not success:
                print("Backup failed. Continue anyway? (y/n)")
                print(self.prompt_char, end="", flush=True)
                backup_input = self.input_shift_buffer("edit").lower()
                if backup_input != "y":
                    exit()

    def backup_wallpaper_folder(self, wallpaper):
        print(f"Creating a backup of {wallpaper} in {os.path.dirname(os.path.realpath(__file__))}/backups")
        try:
            if os.name == "nt":
                print("Running on Windows. Using xcopy to create backup ...")
                os.system(f"xcopy {self.__KOMOREBI_WALLPAPER_DIRS_PATH}\\{wallpaper} {os.path.dirname(os.path.realpath(__file__))}\\backups \\E \\I \\Y \\H")
            else:
                print("Running on an OS other than Windows. Using cp to create backup ...")
                os.system(f"sudo cp -r {self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wallpaper} {os.path.dirname(os.path.realpath(__file__))}/backups")
        except Exception as er:
            print("[ERROR]")
            print(er)
            print(f"[ERROR] Could not create backup of {wallpaper} in {os.path.dirname(os.path.realpath(__file__))}/backups")
            print("Trying to create backup with shutil")
            # Try creating the backup with shutil
            try:
                shutil.copytree(f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wallpaper}", f"{os.path.dirname(os.path.realpath(__file__))}/backups/{wallpaper}")
            except Exception as e:
                print("[ERROR]")
                print(e)
                print(f"[ERROR] Could not create backup of {wallpaper} in {os.path.dirname(os.path.realpath(__file__))}/backups")
                print("If you really need to create a backup before renaming the folder, try running the script as root/administrator")
                print("Otherwise, create the backup manually and then next time you run the script, you can rename the folder without creating a backup")

                return False
    
        return True
    
    def get_tags(self):
        """Gets the tags which are commonly used in the wallpaper names. Tags are defined as any word that is used in 2 or more wallpaper names.
        Tags are separated by a dash (-) in the wallpaper name.
        
        Returns:
            list: A list of tags.
        """

        tags = []
        for wp in self.wallpapers:
            wp_tags = wp.split("-")
            if len(wp_tags) > 1:
                tags += wp_tags
        tags.sort()
        real_tags = []
        right_pointer = 0
        for index, tag in enumerate(tags):
            if index < right_pointer:
                continue
            if tag == "":
                continue
            # Check how many proceeding tags are the same
            num_same = 0
            while index + num_same + 1 < len(tags) and tags[index + num_same + 1] == tag:
                num_same += 1
            # 2 or more instances of the tag being used means it is a real tag
            if num_same >= 2:
                real_tags.append(tag)

            # Skip ahead to the next unique tag by moving the right pointer
            right_pointer += num_same + 1
        
        return real_tags

    def rename_wallpaper(self, wallpaper):
        tags = self.get_tags()
        print(f"Tags found: {', '.join(tags)}")

        print(f"Enter new name for '{colored(wallpaper, 'green')}'")
        print(self.prompt_char, end="", flush=True)
        new_name = self.input_shift_buffer("edit").strip()
        illegal_chars = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
        while new_name == "" or new_name in self.wallpapers or any(char in new_name for char in illegal_chars):
            if new_name == "":
                print("Name cannot be empty")
            elif new_name in self.wallpapers:
                print("Name already exists")
            elif any(char in new_name for char in illegal_chars):
                print("Name cannot contain any of the following characters: " + ", ".join(illegal_chars))
            print("Try again")
            print(self.prompt_char, end="", flush=True)
            new_name = self.input_shift_buffer("edit").strip()
        
        print(f"Renaming '{wallpaper}' to '{new_name}' ...")

        # Ask if user wants to make a backup copy of the wallpaper folder in project directory
        self.ask_for_backup(wallpaper)

        print(f"Renaming '{colored(wallpaper, 'green')}' to '{colored(new_name, 'green')}'\n")
        self.kill_komorebi()
        os.rename(f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{wallpaper}", f"{self.__KOMOREBI_WALLPAPER_DIRS_PATH}/{new_name}")
        self.set_wallpaper(new_name)
        self.start_komorebi()

        # Update references to the wallpaper in the favorites file if it is in favorites
        if wallpaper in self.favorites:
            print(f"Updating references to '{colored(wallpaper, 'green')}' in favorites file ...")
            self.favorites.remove(wallpaper)
            self.favorites.append(new_name)
            with open(self.__FAVORITES_FILE_PATH, "w") as favorites_file:
                for favorite in self.favorites:
                    favorites_file.write(favorite + "\n")

        print("Done.\n")

    # ----------------------------

    def print_prompt_and_cur_input(self):
        print(f"Active Wallpaper: {colored(self.get_active_wallpaper(), 'green')}")
        print(self.instructions)
        print(self.prompt_char + self.cur_input, end="", flush=True)

    def on_key_press(self, event):
        if event.name in self.ignore_keys:
            return
        
        if event.event_type == keyboard.KEY_DOWN:
            # Shift Down turns on shift_pressed flag
            if event.name == 'shift':
                self.shift_pressed = True
            return

        if event.event_type == keyboard.KEY_UP:
            # Shift Up turns off shift_pressed flag
            if event.name == 'shift':
                self.shift_pressed = False

            # Check if the pressed key is backspace or delete and remove the last letter from the current input
            elif event.name == 'backspace' or event.name == 'delete':
                self.cur_input = self.cur_input[:-1]
                self.update_results()

            # TAB and ENTER for selection
            elif event.name == 'enter' or event.name == 'return' or event.name == 'tab':
                wallpaper = self.select_from_results(-1 if event.name == 'tab' else self.cur_result_index)
                if wallpaper:
                    # Current input is cleared after a successful selection
                    self.cur_input = ""
                    
                    self.refresh_with_new(wallpaper)

            # Check if pressed key is up or down arrow and change the current result index
            elif event.name == 'up':
                if self.cur_result_index > 0:
                    self.cur_result_index -= 1
                self.update_results()
            elif event.name == 'down':
                if self.cur_result_index < len(self.cur_results) - 1:
                    self.cur_result_index += 1
                self.update_results()


            # Catch all other keys and add them to the current input
            else:
                if self.shift_pressed:
                    self.cur_input += self.get_shift_variant(event.name)
                else:
                    self.cur_input += event.name
                self.update_results()

    def kill_komorebi(self):
        print("Killing any running instances of Komorebi ...")
        os.system("killall komorebi")

    def start_komorebi(self):
        print("Starting Komorebi ...")
        # Start for each monitor
        config_files = [f for f in os.listdir(self.__KOMOREBI_CONFIG_FILE_PATH.split(self.__KOMOREBI_CONFIG_FILE_NAME)[0]) if ".Komorebi" in f and ".prop" in f]
        for config_file in config_files:
            # run as the user because the script is run as root, but root user does not have same configs as user
            os.system(f"sudo -u {self.get_cur_user()} nohup {self.__KOMOREBI_APP_PATH} {config_file.split('.prop')[0][-1]} > /dev/null 2>&1 &")
        # os.system(f"sudo -u {self.get_cur_user()} nohup {self.__KOMOREBI_APP_PATH} {self.MONITOR_INDEX} > /dev/null 2>&1 &")

    def start(self):
        sleep(.25)
        keyboard.hook(self.on_key_press)
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            # Stop listening for key events
            keyboard.unhook_all()
            exit("\nProgram stopped.")


if __name__ == "__main__":
    # assure script is run as root
    if os.geteuid() != 0:
        exit("Please run this script as root.")
    ui = UI()
    ui.start()

# [KomorebiProperties]
# WallpaperName=reverb_113_lilpeep_xxxtentacion_fallingdown_slowed_reverb___
# TimeTwentyFour=false
# ShowDesktopIcons=false
# EnableVideoWallpapers=true
