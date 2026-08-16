# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import json

from .path_manager import ADDON_NAME

def check_debug_mode():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        meta_json_path = os.path.join(current_dir, "meta.json")
        debug_mode = False

        if os.path.exists(meta_json_path):
            with open(meta_json_path, 'r', encoding='utf-8') as f:
                meta_data = json.load(f) # type:dict
                config = meta_data.get("config", {}) # type:dict
                debug_mode = config.get("debug_mode", False)

        return debug_mode

    except Exception as e:
        print(f"[{ADDON_NAME}] Erorr: {e} ")
        return False
