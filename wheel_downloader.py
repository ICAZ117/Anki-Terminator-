import platform
import struct
import requests
import os
import sys
import zipfile

from .path_manager import ADDON_NAME

# https://github.com/ArniDagur/python-adblock
# https://pypi.org/project/adblock/#files

def download_wheel(output_dir):
    system = platform.system()
    machine = platform.machine()
    bits = struct.calcsize("P") * 8

    if system == "Windows":
        if bits == 64:
            url = "https://files.pythonhosted.org/packages/5d/b5/f769cd99493602ef7514cd0acc3e221702aaa90577410633533acd7d757c/adblock-0.6.0-cp37-abi3-win_amd64.whl"
        else:
            url = "https://files.pythonhosted.org/packages/99/6e/8d172b16147a58f5c0c4b60efb9e8b3333628a10df3fc4c0c1fbc7ea0934/adblock-0.6.0-cp37-abi3-win32.whl"
    elif system == "Linux":
        if machine in ["aarch64", "arm64"]:
            url = "https://files.pythonhosted.org/packages/cb/3f/2eed1a5a7ef27d745b97f0f2d3c7544f4e37fdef8bc198f1b91cf3268ba9/adblock-0.6.0-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"
        elif machine in ["armv7l", "arm"]:
            url = "https://files.pythonhosted.org/packages/bd/af/b43dd38bf8c2fae093b621069394cc098e01e853bd8142b434e5955c3442/adblock-0.6.0-cp37-abi3-manylinux_2_17_armv7l.manylinux2014_armv7l.whl"
        elif machine == "x86_64":
            url = "https://files.pythonhosted.org/packages/06/26/39fad77ba6fe8bd5b1c5ebe411ea84a768075f40caa5400e889678de39b3/adblock-0.6.0-cp37-abi3-manylinux_2_12_x86_64.manylinux2010_x86_64.whl"
        else:
            url = None
    elif system == "Darwin":
        if bits == 64:
            url = "https://files.pythonhosted.org/packages/82/51/fef5e4c2c184e35d6dd47eecf2068fb9509f1447965813ff489bac7ab3f6/adblock-0.6.0-cp37-abi3-macosx_10_9_x86_64.macosx_11_0_arm64.macosx_10_9_universal2.whl"
        else:
            url = "https://files.pythonhosted.org/packages/23/db/9dd1e59fb4229904a60db01f7aa84e34577d938f996dc394eb35c83ebe34/adblock-0.6.0-cp37-abi3-macosx_10_7_x86_64.whl"
    else:
        url = None

    if not url:
        return None

    extract_dir = os.path.join(output_dir, "adblock")

    if os.path.exists(extract_dir):
        parent_dir = os.path.dirname(extract_dir)
        sys.path.insert(0, parent_dir)
        return None

    os.makedirs(output_dir, exist_ok=True)
    filename = url.split("/")[-1]
    output_path = os.path.join(output_dir, filename)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)

        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        if extract_dir not in sys.path:
            parent_dir = os.path.dirname(extract_dir)
            sys.path.insert(0, parent_dir)

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")



def make_adblock_engine():
    from .make_subfolder import make_subfolder_and_get_path
    subfolder_path = make_subfolder_and_get_path()
    if not subfolder_path:
        return

    output_dir = os.path.join(subfolder_path, "py_adblock")
    easylist_path = os.path.join(os.path.dirname(__file__), "easylist.txt")
    engine_cache_path = os.path.join(output_dir, "adblock_engine.bin")

    download_wheel(output_dir)

    try:
        import adblock  # type: ignore
    except ImportError as e:
        print(f"[{ADDON_NAME}] Error: {e}")
        return None


    if os.path.exists(engine_cache_path):
        try:
            engine = adblock.Engine(adblock.FilterSet())
            engine.deserialize_from_file(engine_cache_path)
            return engine
        except Exception as e:
            print(f"[{ADDON_NAME}] Cache load failed, rebuilding: {e}")

    if not os.path.exists(easylist_path):
        print(f"[{ADDON_NAME}] EasyList not found at {easylist_path}")
        return None

    try:
        filter_set = adblock.FilterSet()
        with open(easylist_path, "r", encoding="utf-8") as f:
            filter_set.add_filter_list(f.read())

        engine = adblock.Engine(filter_set)

        engine.serialize_to_file(engine_cache_path)

        return engine

    except Exception as e:
        print(f"[{ADDON_NAME}] Error during engine creation: {e}")
        return None