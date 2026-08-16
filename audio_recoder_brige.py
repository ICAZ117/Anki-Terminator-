# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import uuid
import base64
import wave
from urllib.parse import urlparse
from os.path import join, dirname, exists

try:
    from PyQt6.QtCore import QObject, pyqtSlot, QUrl
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
    from PyQt6.QtCore import QFile, QIODevice
except:
    from aqt.qt import QObject, pyqtSlot, QUrl
    from aqt.qt import QWebEngineView
    from aqt.qt import QWebEnginePage
    from aqt.qt import QFile, QIODevice

from .path_manager import USER_FILES, ADDON_NAME
from .audio_wav_to_mp3 import try_use_lame_wav_to_mp3



#MARK:RecordingBridge
class AudioRecordingBridge(QObject):

    def __init__(self, page:QWebEnginePage):
        super().__init__(page)
        self.page = page
        self._recordings = {}


    def parse_recording_format(self, mime_type:str):
        default_format = {
            "mime_type": mime_type or "audio/pcm;rate=44100;channels=1;format=s16le",
            "base_type": "audio/pcm",
            "sample_rate": 44100,
            "channels": 1,
            "sample_width": 2,
        }

        if not mime_type:
            return default_format

        parts = []
        for part in mime_type.split(";"):
            if part.strip():
                parts.append(part.strip())

        if not parts:
            return default_format

        base_type = parts[0].lower()
        format_info = dict(default_format)
        format_info["mime_type"] = mime_type
        format_info["base_type"] = base_type

        for part in parts[1:]:
            part:str
            if "=" not in part:
                continue

            items = part.split("=", 1)
            key = items[0].strip().lower()
            value = items[1].strip().lower()

            if key == "rate":
                try:
                    format_info["sample_rate"] = max(1, int(value))
                except ValueError:
                    pass
            elif key == "channels":
                try:
                    format_info["channels"] = max(1, int(value))
                except ValueError:
                    pass
            elif key == "format" and value == "s16le":
                format_info["sample_width"] = 2

        return format_info


    def guess_extension_from_url(self, audio_url:str):
        if not audio_url:
            return ""

        try:
            parsed_url = urlparse(audio_url)
            _, extension = os.path.splitext(parsed_url.path)
        except Exception:
            return ""

        extension_lower = extension.lower()
        supported_extensions = {
            ".mp3",
            ".wav",
            ".ogg",
            ".oga",
            ".flac",
            ".aac",
            ".m4a",
            ".mp4",
            ".opus",
            ".webm",
        }

        if extension_lower in supported_extensions:
            return extension_lower

        return ""


    def make_download_filename(self, mime_type, audio_url=""):
        unique_id = uuid.uuid4().hex
        extention = self.guess_extension_from_url(audio_url)

        if not extention:
            lower_mime_type = (mime_type or "").lower()

            if "audio/pcm" in lower_mime_type or "wav" in lower_mime_type:
                extention = ".wav"
            elif "mpeg" in lower_mime_type or "mp3" in lower_mime_type:
                extention = ".mp3"
            elif "x-m4a" in lower_mime_type or "m4a" in lower_mime_type or "audio/mp4" in lower_mime_type:
                extention = ".m4a"
            elif "aac" in lower_mime_type:
                extention = ".aac"
            elif "flac" in lower_mime_type:
                extention = ".flac"
            elif "opus" in lower_mime_type:
                extention = ".opus"
            elif "ogg" in lower_mime_type:
                extention = ".ogg"
            else:
                extention = ".webm"

        return f"{unique_id}{extention}"


    # def make_output_path(self, mime_type, audio_url=""):
    #     file_name = self.make_download_filename(mime_type, audio_url)

    #     recording_dir = join(dirname(__file__), USER_FILES, "audio_recordings")
    #     if not exists(recording_dir):
    #         os.makedirs(recording_dir)

    #     audio_path = join(recording_dir, file_name)

    #     return audio_path


    def make_output_path(self, mime_type, audio_url=""):
        file_name = self.make_download_filename(mime_type, audio_url)

        recording_dir = join(dirname(__file__), USER_FILES, "audio_recordings")

        INT_MAX_CACHE_FILE = 3

        if not exists(recording_dir):
            os.makedirs(recording_dir)

        else:
            all_files = []
            for name in os.listdir(recording_dir):
                full_path = join(recording_dir, name)

                if os.path.isfile(full_path):
                    all_files.append(full_path)

            all_files.sort(key= os.path.getmtime)

            while len(all_files) >= INT_MAX_CACHE_FILE:
                # 古いﾌｧｲﾙを削除
                oldest_file = all_files.pop(0)
                os.remove(oldest_file)

        audio_path = join(recording_dir, file_name)
        return audio_path




    # --- .js -------

    @pyqtSlot(str, str)
    def onRecording(self, session_id, mime_type):
        format_info = self.parse_recording_format(mime_type)
        self._recordings[session_id] = {
            "mime_type": format_info["mime_type"],
            "format": format_info,
            "chunks": [],
            "path": self.make_output_path(format_info["mime_type"], ""),
        }

    @pyqtSlot(str, str, str)
    def downloadAudioUrl(self, session_id, audio_url, mime_type):
        try:
            self._recordings.pop(session_id, None)

            if not audio_url:
                return

            suggested_file_name = self.make_download_filename(mime_type, audio_url)
            self.page.download(QUrl(audio_url), suggested_file_name)

        except Exception as e:
            print(f"[{ADDON_NAME}] downloadAudioUrl Error: {e}")


    @pyqtSlot(str, str)
    def appendRecChunk(self, session_id, base64_chunk):
        recording = self._recordings.get(session_id)

        if not recording or not base64_chunk:
            return

        try:
            recording["chunks"].append(base64.b64decode(base64_chunk))

        except Exception as e:
            print(f"[{ADDON_NAME}] Error-decode: {e}")


    @pyqtSlot(str)
    def endRecord(self, session_id):
        recording = self._recordings.pop(session_id, None)
        if not recording:
            return

        audio_bytes = b"".join(recording["chunks"])
        if not audio_bytes:
            return

        try:
            format_info = recording.get("format", {})

            if format_info.get("base_type") == "audio/pcm":
                with wave.open(recording["path"], "wb") as audio_file:
                    audio_file.setnchannels(format_info.get("channels", 1))
                    audio_file.setsampwidth(format_info.get("sample_width", 2))
                    audio_file.setframerate(format_info.get("sample_rate", 44100))
                    audio_file.writeframes(audio_bytes)

                mp3_file_path = os.path.splitext(recording["path"])[0] + ".mp3"

                if try_use_lame_wav_to_mp3(recording["path"], mp3_file_path):
                    print(f"[{ADDON_NAME}] mp3 success: {mp3_file_path}")
                    if os.path.exists(recording["path"]):
                        os.remove(recording["path"])

                    print(f"[{ADDON_NAME}] try add cards... ")
                    file_url = QUrl.fromLocalFile(mp3_file_path)
                    self.page.download(file_url, os.path.basename(mp3_file_path))

                else:
                    print(f"[{ADDON_NAME}] mp3 failed: {recording['path']}")

            else:
                with open(recording["path"], "wb") as audio_file:
                    audio_file.write(audio_bytes)
            print(f"[{ADDON_NAME}] save success: {recording['path']}")

        except Exception as e:
            print(f"[{ADDON_NAME}] save Error: {e}")

    @pyqtSlot(str)
    def onRecError(self, message):
        print(f"[{ADDON_NAME}] reportRecordingError: {message}")

    # --- .js -------

_cache_qweb_and_audio_js_code = None

def inject_audio_recording_javascript(webpage:QWebEnginePage):
    try:
        global _cache_qweb_and_audio_js_code

        if _cache_qweb_and_audio_js_code is None:

            qwebchannel_path = ":/qtwebchannel/qwebchannel.js"
            jsfile = QFile(qwebchannel_path)

            if not jsfile.open(QIODevice.OpenModeFlag.ReadOnly):
                print(f"[{ADDON_NAME}] Error, not found qwebchannel.js: {qwebchannel_path}")
                return

            qwebchannel_code = bytes(jsfile.readAll()).decode("utf-8")
            jsfile.close()

            js_audio_recoder = os.path.join(os.path.dirname(__file__), "audio_recoder.js")
            with open(js_audio_recoder, "r", encoding="utf-8") as js_file:
                audio_recoder_code = js_file.read()

            _cache_qweb_and_audio_js_code = qwebchannel_code + audio_recoder_code

        if isinstance(webpage, QWebEnginePage):
            webpage.runJavaScript(_cache_qweb_and_audio_js_code)

    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")
        return

