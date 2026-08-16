# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os

# meta.jsonの"debug_mode"がTrueの場合のみ.tsを.jsへﾄﾗﾝｽﾊﾟｲﾙ
# ﾕｰｻﾞｰ環境では実行しない

def make_js_file():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))

        from .debug_mode import check_debug_mode

        if check_debug_mode():
            import shutil
            import subprocess
            from .path_manager import ADDON_NAME

            print(f"[{ADDON_NAME}] try transpile...")

            tsc_path = shutil.which("tsc")
            node_path = shutil.which("node")

            print(f"[{ADDON_NAME}] tsc_path: {tsc_path}")
            print(f"[{ADDON_NAME}] node_path: {node_path}")

            result = subprocess.run(
                    [
                    tsc_path,
                    os.path.join(current_dir, "audio_recoder.ts")
                    ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[{ADDON_NAME}] transpile success!")
            else:
                print(f"[{ADDON_NAME}] transpile Error:")
                print(f"[{ADDON_NAME}] stdout:", result.stdout)
                print(f"[{ADDON_NAME}] stderr:", result.stderr)
                print(f"[{ADDON_NAME}] returncode:", result.returncode)

    except Exception as e:
        print(f"[AnkiTerminator] Error: {e}")