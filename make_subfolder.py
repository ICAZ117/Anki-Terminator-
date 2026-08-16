# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import json

from .path_manager import ADDON_NAME

# subfolder name
MAIN_MY_ADDON_FOLDER_NAME = "Anki Terminator Subfolder"
META_JSON_ADDON_NAME = "Subfolder for Anki Terminator V2 by Shige"
GREETING = "Hi I'm developer Shige, thanks for using AnkiTerminator."

#MARK: tree

# addons21/
# └── Subfolder/
#     ├── __init__.py
#     ├── meta.json
#     └── user_files/

# addons21
ADDONS_FOLDER_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.basename(ADDONS_FOLDER_PATH) == "addons21":
    print(f"[{ADDON_NAME}] addons21 fine: {ADDONS_FOLDER_PATH}")
else:
    raise RuntimeError(f"[{ADDON_NAME}] Error: this path not addons21")

# my add-on folder
MY_ADDON_PATH = os.path.join(ADDONS_FOLDER_PATH, MAIN_MY_ADDON_FOLDER_NAME)

# user_files
USER_FILES_FOLDER_NAME = "user_files"
MY_ADDON_USER_FILES_PATH = os.path.join(MY_ADDON_PATH, USER_FILES_FOLDER_NAME)

# __init__.py
MY_ADDON_INIT_PATH = os.path.join(MY_ADDON_PATH, "__init__.py")

# meta.json
MY_ADDON_META_JSON_PATH = os.path.join(MY_ADDON_PATH, "meta.json")

META_JSON_FILE = {
    "name": META_JSON_ADDON_NAME,
    "author": "Shigeyuki",
    "homepage": "https://shigeyukey.github.io/shige-addons-wiki/contact.html",
}

# config.json
MY_ADDON_CONFIG_JSON_PATH = os.path.join(MY_ADDON_PATH, "config.json")

CONFIG_JSON_FILE = {}

MY_ADDON_CONFIG_MD_PATH = os.path.join(MY_ADDON_PATH, "config.md")


STR_CONFIG_MD_FILE = f"""\
{GREETING}

This folder is a subfolder automatically created by the add-on. Some files may cause errors if they are deleted or updated while they are stored in the add-on folder, this folder is intended for the add-on to safely store and use them.

If you no longer need the original add-on or if you wish to completely delete the data please delete it manually. Note: If you delete this subfolder while the original add-on is running an error may occur and the process may fail, in that case please disable or delete the original add-on then restart Anki and try again. (or press and hold the Shift key to launch Anki in safe mode.) If you have any questions please contact me.
"""



#MARK: make dirs
def make_subfolder_and_get_path():
    try:
        os.makedirs(MY_ADDON_PATH, exist_ok=True)
        os.makedirs(MY_ADDON_USER_FILES_PATH, exist_ok=True)

        # __init__.py (empty)
        if not os.path.exists(MY_ADDON_INIT_PATH):
            open(MY_ADDON_INIT_PATH, "a").close()

        # meta.json (add-on name)
        if not os.path.exists(MY_ADDON_META_JSON_PATH):
            with open(MY_ADDON_META_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(META_JSON_FILE, f, ensure_ascii=False)

        # config.json (empty)
        if not os.path.exists(MY_ADDON_CONFIG_JSON_PATH):
            with open(MY_ADDON_CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(CONFIG_JSON_FILE, f, ensure_ascii=False)

        # config.md (description)
        if not os.path.exists(MY_ADDON_CONFIG_MD_PATH):
            with open(MY_ADDON_CONFIG_MD_PATH, "w", encoding="utf-8") as f:
                f.write(STR_CONFIG_MD_FILE)

        return MY_ADDON_USER_FILES_PATH

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")
        return ""

