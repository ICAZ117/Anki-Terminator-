# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import subprocess

from .path_manager import ADDON_NAME


def try_use_lame_wav_to_mp3(wav_file_path, mp3_file_path):

    try:
        from aqt.utils import startup_info
        from aqt.sound import _packagedCmd, retryWait

        is_error = False

        cmd = ["lame", wav_file_path, mp3_file_path, "--noreplaygain", "--quiet"]
        cmd, env = _packagedCmd(cmd)
        try:
            retcode = retryWait(subprocess.Popen(cmd, startupinfo=startup_info(), env=env))
        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")
            is_error = True

        if retcode != 0:
            print(f"[{ADDON_NAME}] Error: retcode != 0:")
            is_error = True

        if not is_error and os.path.exists(mp3_file_path):
            return True
        else:
            return False

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")
        return False