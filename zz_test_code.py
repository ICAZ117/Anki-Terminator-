import os
import requests
from urllib.parse import urlparse
try:
    from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
except:
    from aqt.qt import QWebEngineUrlRequestInterceptor

class AudioDownloader(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()

        if any(url.endswith(ext) for ext in [".mp3", ".wav", ".m4a", ".ogg"]):
            print(f"[{ADDON_NAME}] found audio: {url}")
            self.download_file(url)


    def download_file(self, url):
        print(f"[{ADDON_NAME}] try dl...")
        unique_id = uuid.uuid4().hex

        url_path = urlparse(url).path
        _, extention = os.path.splitext(url_path)

        file_name = (
                f"ankiTerminatorTTS_{unique_id}"
                f"{extention}"
                )

        recording_dir = join(dirname(__file__), USER_FILES, "audio_recordings")
        if not exists(recording_dir):
            os.makedirs(recording_dir)

        audio_path = join(recording_dir, file_name)

        response = requests.get(url)
        with open(audio_path, "wb") as f:
            f.write(response.content)

        print(f"[{ADDON_NAME}] Save Success: {url_path}")


    def download_file(self, url):
        print(f"[{ADDON_NAME}] try dl...")
        unique_id = uuid.uuid4().hex

        try:
            from .bundle.filetype import filetype

            response = requests.get(url)
            response.raise_for_status()

            kind = filetype.match(response.content)

            extension = ""
            if kind:
                extension = kind.extension
            else:
                url_path = urlparse(url).path
                _, extension = os.path.splitext(url_path)

            file_name = f"ankiTerminatorTTS_{unique_id}{extension}"

            recording_dir = join(dirname(__file__), USER_FILES, "audio_recordings")
            if not exists(recording_dir):
                os.makedirs(recording_dir)

            audio_path = join(recording_dir, file_name)

            with open(audio_path, "wb") as f:
                f.write(response.content)

            print(f"[{ADDON_NAME}] Save Success: {audio_path}")

        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")
