# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import time
import shutil
import random
import re
from os.path import join, dirname, exists

from anki.cards import Card
from aqt import mw, gui_hooks
from aqt.utils import openLink, tooltip
from aqt.webview import AnkiWebView

try:
    from PyQt6.QtWidgets import (
        QCheckBox, QComboBox, QDockWidget, QLabel, QLineEdit,
        QMenu, QPushButton, QToolBar, QVBoxLayout, QWidget, QGraphicsOpacityEffect)
    from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QUrl, QMimeData
    from PyQt6.QtGui import QClipboard, QFontMetrics, QKeySequence, QPixmap, QCursor, QAction
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEngineContextMenuRequest, QWebEnginePage, QWebEngineProfile, QWebEngineSettings)
    from PyQt6.QtWebChannel import QWebChannel
except Exception as e:
    print(f"Error: {e}")

    from aqt.qt import (
        QCheckBox, QComboBox, QDockWidget, QLabel, QLineEdit,
        QMenu, QPushButton, QToolBar, QVBoxLayout, QWidget, QGraphicsOpacityEffect)
    from aqt.qt import Qt, pyqtSignal, QSize, QTimer, QUrl, QMimeData
    from aqt.qt import QClipboard, QFontMetrics, QKeySequence, QPixmap, QCursor, QAction
    from aqt.qt import QWebEngineView
    from aqt.qt import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    from aqt.qt import QWebChannel
    try:
        from aqt.qt import QWebEngineContextMenuRequest
    except ImportError:
        from PyQt5.QtWebEngineWidgets import QWebEngineContextMenuData as QWebEngineContextMenuRequest


from .config.PopUpAnkiConfig import (
        SOUND_SYSTEM, set_this_addon_Config, CONFIG_FOLDER,
        SOUND_SELECT, SOUND_OPENLINK, SOUND_SYSTEM, THEME_CHANGE)
from .context_menu.download_files import (
    on_download_requested, set_context_menu_v2, reset_selected_note_data)
from .path_manager import (BING_CHAT, CHAT_GPT, COOKIE_DATA, GOOGLE_BARD, IMAGE_FX, NOW_LOADING,
                            SHOW_ANSWER_PNG, HIDE_HIGHT, USER_FILES, CUSTOM_AI,
                            DEEP_SEEK, PERPLEXITY, CLAUDE,
                            GROK_AI, DUCK_AI, GOOGLE_AI_MODE,
                            ADDON_NAME
                            )
from .shigetr import shige_tr, qtip_style
from .context_menu.add_fields import add_context_menu
from .audio_recoder_brige import AudioRecordingBridge, inject_audio_recording_javascript
from .ad_blocker import set_add_blocekr, adblock_load_time_checker
from .make_subfolder import make_subfolder_and_get_path, MAIN_MY_ADDON_FOLDER_NAME


web_shortcut = None
completely_close_sidebar = None
list_new_dialogs = []


#MARK:ClickableLabel
class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().leaveEvent(event)

try:
    from PyQt6.QtWebEngineCore import QWebEngineScript
except Exception as e:
    print(f"[{ADDON_NAME}] Error: {e} ")
    from aqt.qt import QWebEngineScript


script = QWebEngineScript()
script.setName("AudioDownloader")
script.setSourceCode("document.body.style.filter = 'grayscale(100%)';")
script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
script.setRunsOnSubFrames(True)





#MARK:WebEnginePage
class CustomWebEnginePage(QWebEnginePage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        config = mw.addonManager.getConfig(__name__)
        self.enable_auto_dl_audio = config.get("enable_auto_dl_audio", False)
        self.enable_adblocker = config.get("enable_adblocker", False)

        # Initialize audio components to None (for safe cleanup)
        self.audio_recording_bridge = None
        self.audio_recording_channel = None
        self.stop_timer = None


        if self.enable_auto_dl_audio:
            self.audio_recording_bridge = AudioRecordingBridge(self)
            self.audio_recording_channel = QWebChannel(self)
            self.audio_recording_channel.registerObject(
                "shigeAudioRecorder", self.audio_recording_bridge
            )
            self.setWebChannel(self.audio_recording_channel)

            self.recentlyAudibleChanged.connect(self.handle_audio_state)

            self.stop_timer = QTimer(self)
            self.stop_timer.setSingleShot(True)
            self.stop_timer.timeout.connect(self._actual_stop_recording)

        if self.enable_adblocker:
            # adblock ckecker (debug only)
            adblock_load_time_checker(self)


        if self.enable_auto_dl_audio:
            self.loadFinished.connect(lambda:inject_audio_recording_javascript(self))



    def createWindow(self, _type):
        print(_type)

        profile = self.profile()

        # mw.AnkiTerminator_new_dialog = new_dialog = QWidget(None)

        mw.AnkiTerminator_new_dialog = new_dialog = QWidget(dock_content)
        new_dialog.setWindowFlags(Qt.WindowType.Window)

        list_new_dialogs.append(new_dialog)
        mw.AnkiTerminator_new_dialog = new_dialog

        new_dialog.setWindowTitle("New Dialog")
        new_dialog.resize(700, 600)
        web_view = CustomWebEngineView(new_dialog)
        new_page = CustomWebEnginePage(profile, web_view)

        web_view.setPage(new_page)

        layout = QVBoxLayout(new_dialog)
        layout.addWidget(web_view)
        new_dialog.setLayout(layout)

        # if self.enable_auto_dl_audio:
        #     new_page.loadFinished.connect(lambda:inject_audio_recording_javascript(web_view))

        new_dialog.closeEvent = lambda event: self.cleanup(new_dialog, web_view, new_page, event)

        QTimer.singleShot(0, new_dialog.show)

        return new_page


    def handle_audio_state(self, audible):
        if not self.enable_auto_dl_audio:
            return

        if audible:
            self.stop_timer.stop() # cancel
            self.runJavaScript(
                "window.shigeAudioRecorder && window.shigeAudioRecorder.startRecording();"
            )
        else:
            self.stop_timer.start(2000) # no audible check

    def _actual_stop_recording(self):
        self.runJavaScript(
            "window.shigeAudioRecorder && window.shigeAudioRecorder.stopRecording();"
        )

    #MARK:jsConsoleMessage
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        return

        # ﾃﾞﾊﾞｯｸﾞ用
        try:
            if level == QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel:
                level_str = "info"
            elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
                level_str = "warning"
            elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
                level_str = "error"
            else:
                level_str = str(level)
        except Exception:
            level_str = str(level)
        print(f"[{ADDON_NAME}-JS][{level_str}] {message} (Line {lineNumber}, Source: {sourceID})")


    def cleanup(self,
                dialog: QWidget, web_view: 'CustomWebEngineView', page: 'CustomWebEnginePage', event):
        # ｳｨｼﾞｪｯﾄを閉じても残ることがある
        try:
            try:
                if self.enable_auto_dl_audio:
                    page.recentlyAudibleChanged.disconnect(page.handle_audio_state)
                    if page.stop_timer and page.stop_timer.isActive():
                        page.stop_timer.stop()
                    page.setWebChannel(None)
            except Exception as e:
                print(f"[{ADDON_NAME}] Error: {e} ")

            web_view.setPage(None)
            if page:
                page.deleteLater()
            if web_view:
                web_view.deleteLater()
            if hasattr(mw, 'AnkiTerminator_new_dialog'):
                mw.AnkiTerminator_new_dialog = None

            if dialog in list_new_dialogs:
                list_new_dialogs.remove(dialog)

            event.accept()
        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")
            event.accept()



#MARK:EngineView
class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent #type: ResizableWebView

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        data = self.lastContextMenuRequest()
        if data.editFlags() & QWebEngineContextMenuRequest.EditFlag.CanPaste:
            is_can_paste = True
        else:
            is_can_paste = False


        if not self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            if self.pageAction(QWebEnginePage.WebAction.Back).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Back))
            if self.pageAction(QWebEnginePage.WebAction.Forward).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Forward))
            if self.pageAction(QWebEnginePage.WebAction.Reload).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.Reload))

        if (self.pageAction(QWebEnginePage.WebAction.Paste).isEnabled()
            and is_can_paste):
            menu.addAction(self.pageAction(QWebEnginePage.WebAction.Paste))

        if (not is_can_paste
            and self.pageAction(QWebEnginePage.WebAction.CopyImageToClipboard).isEnabled()
            and data.mediaType() !=  QWebEngineContextMenuRequest.MediaType.MediaTypeNone):
            menu.addAction(self.pageAction(QWebEnginePage.WebAction.CopyImageToClipboard))

            menu.addSeparator()
            reset_selected_note_data()
            set_context_menu_v2(self, menu)
            menu.addSeparator()

        if self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            menu.addAction(self.pageAction(QWebEnginePage.WebAction.Copy))

            custom_action = QAction("🧩Set text to AnkiTerminator", self)
            custom_action.triggered.connect(
                lambda: self.contextMenu(self, menu))
            menu.addAction(custom_action)



        if data.linkUrl().isValid() and not data.linkUrl().isEmpty():
            menu.addSeparator()
            if self.pageAction(QWebEnginePage.WebAction.DownloadLinkToDisk).isEnabled():
                menu.addAction(self.pageAction(QWebEnginePage.WebAction.DownloadLinkToDisk))
            menu.addSeparator()


        menu.addSeparator()
        text_action = QAction("❔️📥Add text to card", menu)
        text_action.triggered.connect(
            lambda: openLink(
        "https://shigeyukey.github.io/shige-addons-wiki/AnkiTerminator/anki_terminator_00.html#right-click-actions"))
        # text_action.setEnabled(False)
        menu.addAction(text_action)

        print(f"editFlags: {data.editFlags()}")
        print(f"mediaFlags: {data.mediaFlags()}")
        print(f"mediaType: {data.mediaType()}")
        print(f"linkUrl: {data.linkUrl()}")
        print(f"selectedText: {data.selectedText()}")

        if not is_can_paste and self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            selected = self.page().selectedText()
            print(f"text: {selected}")
            menu.addSeparator()
            add_context_menu(self, menu)
            menu.addSeparator()

        from .context_menu.image_widget import make_image_ai_widget, send_prompts, CustomImageWidget
        menu.addSeparator()
        imageFX_action = QAction("🖼️ImageFX", menu)
        imageFX_action.triggered.connect(lambda: make_image_ai_widget(self.parent_window.webpage))
        menu.addAction(imageFX_action)

        if not is_can_paste and self.pageAction(QWebEnginePage.WebAction.Copy).isEnabled():
            selected = self.page().selectedText()
            print(f"text: {selected}")
            send_imageFX_action = QAction("Send Prompt to ImageFX", menu)
            send_imageFX_action.triggered.connect(lambda: send_prompts(selected))
            menu.addAction(send_imageFX_action)
            if (not hasattr(mw, "AnkiTerminator_image_Ai_dialog")
                or
                hasattr(mw, "AnkiTerminator_image_Ai_dialog")
                and not isinstance(mw.AnkiTerminator_image_Ai_dialog, CustomImageWidget)):
                send_imageFX_action.setEnabled(False)

        menu.addSeparator()


        # for ankiwebview inspector
        if mw.addonManager.getConfig(__name__).get("Debug", False):
            gui_hooks.webview_will_show_context_menu(self, menu)

        menu.exec(event.globalPos())

    def contextMenu(self, webview: AnkiWebView, menu: QMenu,*args,**kwargs):
        selected = webview.page().selectedText()
        if not selected:
            return
        self.parent_window.set_last_text(selected)


#MARK:ResizableWebView
class ResizableWebView(QWidget):
    def __init__(self, name, url, parent=None):
        super().__init__(parent)

        # ----------🍪 Cookie monster ---------------
        try:
            config = mw.addonManager.getConfig(__name__)
            enable_browser_cookies = config.get("enable_browser_cookies", "FirstRun")

            if enable_browser_cookies == "FirstRun":
                from .shige_dialogs.shige_info_v2 import ShigeInfo

                result = ShigeInfo.question(
                    parent=None,
                    text="""\
[ 🤖Anki Terminator V2 Setup ]
Do you want to Save the Cookies?
1. [🍪Save Cookies] Keep cookies and login info.
2. [👤Anonymous] Delete cookies, restart will require re-login.
                    """,
                    yes_text="Yes (🍪Save Cookies)",
                    no_text="No (👤Anonymous)",
                    # Width: 431, Height: 171
                    width=450,
                    height=150,
                    timeout_seconds=300
                )

                if result:
                    enable_browser_cookies = is_enable = True
                    tooltip("🍪Save Cookies mode")
                else:
                    enable_browser_cookies = is_enable = False
                    tooltip("👤Anonymous mode")

                config["enable_browser_cookies"] = is_enable
                mw.addonManager.writeConfig(__name__, config)

        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")
            enable_browser_cookies = False

        old_ver_cookie_folder = join(dirname(__file__), USER_FILES, COOKIE_DATA)
        subfolder_path = make_subfolder_and_get_path()
        new_cookie_folder = join(subfolder_path, COOKIE_DATA)

        if exists(subfolder_path):
            try:
                # 新しいﾊﾞｰｼﾞｮﾝではｸｯｷｰを外部ｻﾌﾞﾌｫﾙﾀﾞへ移動(更新時のｴﾗｰを避ける)
                if exists(old_ver_cookie_folder) and not exists(new_cookie_folder):
                    shutil.move(old_ver_cookie_folder, new_cookie_folder)
                    print(f"[{ADDON_NAME}] >> Cookie folder moved to -> {new_cookie_folder}")
            except Exception as e:
                print(f"[{ADDON_NAME}] Error: {e}")

        else:
            # subfolder not found?
            enable_browser_cookies = False

        if enable_browser_cookies:
            # ｸｯｷｰﾓｰﾄﾞ
            self.cookie_profile = QWebEngineProfile("my_profile", self)
            print(f"[{ADDON_NAME}] StoragePath: {self.cookie_profile.persistentStoragePath()}")
            self.cookie_profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            if not exists(new_cookie_folder):
                os.makedirs(new_cookie_folder)

            self.cookie_profile.setPersistentStoragePath(new_cookie_folder)
            print(r"""
Cookie monster! Om nom nom nom nom nom nom...
               _  _
             _/0\/ \_
    .-.   .-` \_/\0/ '-.
   /:::\ / ,_________,  \
  /\:::/ \  '. (:::/  `'-;
  \ `-'`\ '._ `"'"'\__    \
   `'-.  \   `)-=-=(  `,   |
jgs    \  `-"`      `"-`   /
                """)

        else:
            # 匿名ﾓｰﾄﾞ
            # https://doc.qt.io/qt-6/qwebengineprofile.html#details

            self.cookie_profile = QWebEngineProfile("", self) # isOffTheRecord

            self.cookie_profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)

            try:
                if MAIN_MY_ADDON_FOLDER_NAME and (MAIN_MY_ADDON_FOLDER_NAME in new_cookie_folder):
                    if exists(subfolder_path) and exists(new_cookie_folder):
                        shutil.rmtree(new_cookie_folder)
                        print(f"[{ADDON_NAME}] >> cookie deleted: {new_cookie_folder}")
            except Exception as e:
                print(f"[{ADDON_NAME}] Error: {e}")

        # ---------- Cookie monster end ---------------

        if config.get("enable_adblocker", False):
            set_add_blocekr(self.cookie_profile)


        self.last_call = 0
        self.last_card = None
        self.last_text = None
        self.context_action = None
        self.loading = False
        self.last_card_note = None

        self.previous_answer_card_id = None
        self.previous_question_card_id = None

        self.focus_text_area_js = ""

        self.setWindowTitle(name)
        self.setMinimumSize(QSize(300, 300))

        self.webview = CustomWebEngineView(self)

        # ｸﾘｯﾌﾟﾎﾞｰﾄﾞにｺﾋﾟｰ
        settings = self.cookie_profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        # auto play support
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        try:
            # Night Mode Support
            from aqt.theme import theme_manager
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.ForceDarkMode,
                theme_manager.get_night_mode())
        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")


        # ------ now loading icon ------
        self.grey_widget = QWidget()
        addon_path = dirname(__file__)
        icon_path = join(addon_path, NOW_LOADING)
        pixmap = QPixmap(icon_path)
        self.label = ClickableLabel(self.grey_widget)
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.clicked.connect(lambda: openLink("http://patreon.com/Shigeyuki"))
        layout = QVBoxLayout(self.grey_widget)
        layout.addStretch()
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self.grey_widget.setLayout(layout)
        # ----------------------------------

        self.webpage = CustomWebEnginePage(self.cookie_profile, self.webview) # Cookie

        self.webview.loadStarted.connect(self.on_load_started)
        self.webview.loadFinished.connect(self.on_load_finished)
        self.webview.loadFinished.connect(self.inject_javascript)


        self.cookie_profile.downloadRequested.connect(
            lambda download : on_download_requested(download, self))


        self.hide_webview()

        self.webview.setPage(self.webpage)
        self.webpage.featurePermissionRequested.connect(self.on_permission_requested)

        self.webview.load(QUrl(url))

        layout = QVBoxLayout(self)
        self.last_text_toolbar(layout)
        self.make_menu_button(layout)

        layout.addWidget(self.webview)
        layout.addWidget(self.grey_widget)
        layout.setContentsMargins(1, 1, 1, 1)

        self.get_field_text()

        self.setLayout(layout)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)#たぶんいらない

        # closeEventをﾌｯｸしてｵﾌﾞｼﾞｪｸﾄを削除しないようにする
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)#たぶんいらない


        #MARK:hooks
        gui_hooks.webview_will_show_context_menu.append(self.contextMenu)
        gui_hooks.editor_will_show_context_menu.append(self.contextMenu)
        gui_hooks.reviewer_did_show_question.append(self.ChatGPT_hide_webview)
        gui_hooks.reviewer_did_show_answer.append(self.ChatGPT_show_webview)
        gui_hooks.reviewer_will_end.append(self.ChatGPT_show_webview)
        gui_hooks.reviewer_did_show_answer.append(self.show_answer_preload)
        gui_hooks.reviewer_did_show_question.append(self.show_question_preload)

        self.opacity_effect_0 = QGraphicsOpacityEffect(self)
        self.opacity_effect_1 = QGraphicsOpacityEffect(self)


    def on_permission_requested(self, security_origin, feature):
        # audio support
        if feature == QWebEnginePage.Feature.MediaAudioCapture:
            self.webview.page().setFeaturePermission(
                security_origin,
                feature,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

    def remove_all_hooks(self):
        gui_hooks.webview_will_show_context_menu.remove(self.contextMenu)
        gui_hooks.editor_will_show_context_menu.remove(self.contextMenu)
        gui_hooks.reviewer_did_show_question.remove(self.ChatGPT_hide_webview)
        gui_hooks.reviewer_did_show_answer.remove(self.ChatGPT_show_webview)
        gui_hooks.reviewer_will_end.remove(self.ChatGPT_show_webview)
        gui_hooks.reviewer_did_show_answer.remove(self.show_answer_preload)
        gui_hooks.reviewer_did_show_question.remove(self.show_question_preload)


    def inject_javascript(self):
        # inject_audio_recording_javascript(self.webview)

        config = mw.addonManager.getConfig(__name__)
        if not config.get("now_AI_type", False) == CHAT_GPT:
            return
        if not config.get("auto_read_aloud", True):
            return

        # ｱｲﾃﾞｨｱを一部参考
        # https://github.com/3choff/ChatGPT_ReadAloud

        javascript_code = """
let clickedTestIds = new Set();

function findAndClickButton() {
    const conversationTurns = document.querySelectorAll('[data-testid^="conversation-turn-"]');
    let maxTestIdElement = null;
    let maxTestId = -1;
    conversationTurns.forEach(element => {
        const testId = parseInt(element.getAttribute('data-testid').split('-').pop());
        if (testId > maxTestId && !clickedTestIds.has(testId)) {
            maxTestId = testId;
            maxTestIdElement = element;
        }
    });

    if (maxTestIdElement) {
        const button = maxTestIdElement.querySelector('button[aria-label="More actions"]');
        if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {
            button.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true, view: window}));
            button.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, cancelable: true, view: window}));
            clickedTestIds.add(maxTestId);

            setTimeout(() => {
                const menuItem = document.querySelector('[data-testid="voice-play-turn-action-button"]');
                if (menuItem) {
                    menuItem.click();
                }
            }, 500);
        }
    }
}

setInterval(findAndClickButton, 2000);
"""

        self.webview.page().runJavaScript(javascript_code)




    def ChatGPT_hide_webview(self, *args, **kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        if hide:
            self.change_image(SHOW_ANSWER_PNG)
            self.grey_widget.setVisible(True)
            self.webview.setVisible(False)
            self.opacity_effect_0.setOpacity(0)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)


    def ChatGPT_show_webview(self, *args, **kwargs):
        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        if hide:
            self.grey_widget.setVisible(False)
            self.webview.setVisible(True)

            self.opacity_effect_0.setOpacity(1)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)

        elif not self.loading and self.webview.height() == HIDE_HIGHT:
            self.grey_widget.setVisible(False)
            self.webview.setVisible(True)
            self.opacity_effect_0.setOpacity(1)
            self.last_text_edit.setGraphicsEffect(self.opacity_effect_0)

        else:
            pass

    def change_image(self, image_name):
        addon_path = dirname(__file__)
        icon_path = join(addon_path, image_name)
        pixmap = QPixmap(icon_path)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.label.setPixmap(pixmap)

    def load_url(self):
        config = mw.addonManager.getConfig(__name__)
        now_AI_type = config["now_AI_type"]

        if now_AI_type in config["ChatGPT_URL"]:
            ChatGPT_URL = config["ChatGPT_URL"][now_AI_type]
        elif (now_AI_type == CUSTOM_AI
            and not config["Custom_AI_URL"].isspace()):
            ChatGPT_URL = config["Custom_AI_URL"]
        else: # ﾃﾞﾌｫﾙﾄ
            ChatGPT_URL = CHAT_GPT

        self.webview.load(QUrl(ChatGPT_URL))


    def on_load_started(self):
        self.loading = True
        self.hide_webview()

    def on_load_finished(self):
        self.loading = False
        self.show_webview()

    def hide_webview(self):
        self.grey_widget.setVisible(True)
        self.webview.setVisible(False)

    def show_webview(self):
        self.grey_widget.setVisible(False)
        self.webview.setVisible(True)



    def last_text_toolbar(self, layout: QVBoxLayout):
        self.last_text_bar = QToolBar()
        self.last_text_bar.setStyleSheet("QToolBar { margin: 1px; padding: 1px; }")
        layout.addWidget(self.last_text_bar)

        self.make_button(
            "AI", lambda :self.change_AI_type(), self.last_text_bar, True,
            tooltip_text="Quick Change AI")

        config = mw.addonManager.getConfig(__name__)

        self.checkbox = QCheckBox()
        self.checkbox .setStyleSheet("QCheckBox { margin: 1px; padding: 1px; }")
        self.checkbox.stateChanged.connect(self.checkbox_state_changed)
        self.checkbox.setChecked(config["submit_text"])
        self.checkbox.setStyleSheet(qtip_style)
        self.checkbox.setToolTip(shige_tr.check_box_tooltip)
        self.last_text_bar.addWidget(self.checkbox)


        # auto_read_aloud ﾁｪｯｸﾎﾞｯｸｽの追加
        self.auto_read_aloud_checkbox = QCheckBox()
        self.auto_read_aloud_checkbox.setStyleSheet("QCheckBox { margin: 1px; padding: 1px; }")
        self.auto_read_aloud_checkbox.stateChanged.connect(self.auto_read_aloud_checkbox_state_changed)
        self.auto_read_aloud_checkbox.setChecked(config.get("auto_read_aloud", True))
        self.auto_read_aloud_checkbox.setStyleSheet(qtip_style)
        self.auto_read_aloud_checkbox.setToolTip("Auto-read aloud (for ChatGPT only)")
        self.last_text_bar.addWidget(self.auto_read_aloud_checkbox)
        # ------------------------------



        self.last_text_edit = QLineEdit(self.last_text)
        self.last_text_edit.setStyleSheet("QLineEdit { margin: 1px; padding: 1px; }")
        self.last_text_edit.textChanged.connect(self.update_last_text)
        self.last_text_bar.addWidget(self.last_text_edit)


        self.make_button(
            " ⚙️ ", self.option_button_click, self.last_text_bar,
            tooltip_text="⚙️Option")


        if True:
            self.make_button(
                "❔️", self.question_button_click, self.last_text_bar,
                tooltip_text="📖Wiki")

        config = mw.addonManager.getConfig(__name__)

        if not config.get("sidebar_rate_this_clicked", False):
            self.make_button(
                "👍️", self.rate_this_button_click, self.last_text_bar,
                tooltip_text="👍️Rate This"
                )
        else:
            self.make_button(
                "💖", self.patreon_button_click, self.last_text_bar,
                tooltip_text="💖Become a Patron"
                )

    def question_button_click(self):
        openLink(
            "https://shigeyukey.github.io/shige-addons-wiki/AnkiTerminator/anki_terminator_00.html#ai-sidebar")

    def rate_this_button_click(self):
        ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
        if (isinstance(ADDON_PACKAGE, (int, float))
            or (isinstance(ADDON_PACKAGE, str)
            and ADDON_PACKAGE.isdigit())):
            RATE_THIS_URL = f"https://ankiweb.net/shared/review/{ADDON_PACKAGE}"
            openLink(RATE_THIS_URL)
        config = mw.addonManager.getConfig(__name__)
        config["sidebar_rate_this_clicked"] = True
        mw.addonManager.writeConfig(__name__, config)
        PYGsound(SOUND_OPENLINK)

    def patreon_button_click(self):
        openLink("https://www.patreon.com/Shigeyuki")
        PYGsound(SOUND_OPENLINK)

    def auto_read_aloud_checkbox_state_changed(self, state):
        config = mw.addonManager.getConfig(__name__)
        auto_read_aloud = (state == 2)
        config["auto_read_aloud"] = auto_read_aloud
        if auto_read_aloud:
            tooltip("Enabled ChatGPT will auto read aloud! :-)")
        else:
            tooltip("Disabled ChatGPT will auto read aloud :-(")

        mw.addonManager.writeConfig(__name__, config)
        self.webview.reload()


    def checkbox_state_changed(self, state):
        config = mw.addonManager.getConfig(__name__)
        if state == 2:
            config["submit_text"] = True
            tooltip("Enabled auto send prompts! :-)")
        else:
            config["submit_text"] = False
            tooltip("Disabled auto send prompts :-(")
        mw.addonManager.writeConfig(__name__, config)

    def change_AI_type(self,update=True):
        if update:
            from .path_manager import update_theme
            update_theme()
            PYGsound(THEME_CHANGE)
        self.load_url()
        from .update_top_toolbar import change_AI_icon_on_top_tool_bar # 循環ｲﾝﾎﾟｰﾄ
        change_AI_icon_on_top_tool_bar()


    def option_button_click(self):
        set_this_addon_Config()


    def update_last_text(self, text):
        self.last_text = text

    def set_last_text(self, text):
        self.last_text = text
        self.last_text_edit.setText(text)


    def get_field_text(self, card=None):
        config = mw.addonManager.getConfig(__name__)
        if card is None and mw.state == "review":
            card = mw.reviewer.card
        else:
            return
        self.last_card = card
        note = card.note()
        self.last_card_note = note
        note_type = note.note_type()

        if self.is_excluded_note_type(config, note_type):
            return

        first_field_name = self.get_priority_field_name(config, note_type)

        text = card.note()[first_field_name]
        self.set_last_text(text)
    # ---------------------------------------------------


    def get_button_function_pairs(self, config):

        b_name = config["button_name"]

        button_function_pairs = {
            "random_prompt": b_name[0],
            "more_info": b_name[1],
            "baby_explanation": b_name[2],
            "word_origin": b_name[3],
            "make_joke": b_name[4],
            "history": b_name[5],
            "synonym": b_name[6],
            "mnemonic": b_name[7]
        }
        return b_name, button_function_pairs



    def make_menu_button(self, layout: QVBoxLayout):
        config = mw.addonManager.getConfig(__name__)
        b_name, button_function_pairs = self.get_button_function_pairs(config)

        # # ﾎﾞﾀﾝの名前とｱｸｼｮﾝのﾘｽﾄ # 🚨lambdaのﾃﾞﾌｫﾙﾄ引数がうまく機能しない
        # buttons = []
        # for text, name in button_function_pairs.items():
        #     # buttons.append((name, lambda text=text: self.more_function(text)))
        #     buttons.append((name, partial(self.more_function, text)))


        buttons = [
            # ("field", self.field_function),
            (b_name[0], lambda: self.more_function("random_prompt")),
            (b_name[1], lambda: self.more_function("more_info")),
            (b_name[2], lambda: self.more_function("baby_explanation")),
            (b_name[3], lambda: self.more_function("word_origin")),
            (b_name[4], lambda: self.more_function("make_joke")),
            (b_name[5], lambda: self.more_function("history")),
            (b_name[6], lambda: self.more_function("synonym")),
            (b_name[7], lambda: self.more_function("mnemonic")),
        ]

        # ﾂｰﾙﾊﾞｰを作成
        self.toolBar = QToolBar()
        self.toolBar.setStyleSheet("QToolBar { margin: 1px; padding: 1px; }")

        layout.addWidget(self.toolBar)
        layout.setContentsMargins(1, 1, 1, 1)

        self.make_combo_box(button_function_pairs)

        for button_name, action_function in buttons:
            self.make_button(button_name, action_function, self.toolBar)



    def save_selection(self):
        selected_key = self.combo_box.currentData()
        config = mw.addonManager.getConfig(__name__)
        config["default_prompt"] = selected_key
        mw.addonManager.writeConfig(__name__, config)


    def adjust_combo_box_width(self):
        font_metrics = QFontMetrics(self.combo_box.font())
        text = self.combo_box.currentText()
        width = font_metrics.horizontalAdvance(text) + 40
        self.combo_box.setFixedWidth(width)


    def make_combo_box(self, button_function_pairs):
        config = mw.addonManager.getConfig(__name__)
        default_prompt = config.get("default_prompt", "random_prompt")
        self.combo_box = QComboBox()

        for key, value in button_function_pairs.items():
            self.combo_box.addItem(value, key)

        if default_prompt not in button_function_pairs:
            default_prompt = "random_prompt"

        default_index = self.combo_box.findData(default_prompt)
        if default_index != -1:
            self.combo_box.setCurrentIndex(default_index)

        self.combo_box.currentIndexChanged.connect(self.save_selection)
        self.combo_box.currentIndexChanged.connect(self.adjust_combo_box_width)
        self.adjust_combo_box_width()
        self.toolBar.addWidget(self.combo_box)



    def make_button(self, button_name, action_function, toolbar:QToolBar, sound=False, tooltip_text=None):
        action = QAction(button_name, self)
        button = QPushButton(button_name)
        fm = QFontMetrics(button.font())
        width = fm.horizontalAdvance(button_name)
        button.setFixedSize(width + 10, 25)

        action.triggered.connect(action_function)
        button.clicked.connect(action.trigger)

        if sound is False:
            button.clicked.connect(lambda: PYGsound(SOUND_SELECT))


        custom_style_sheet = "QPushButton { margin: 1px; padding: 1px; }"
        if tooltip_text:
            button.setToolTip(tooltip_text)
            custom_style_sheet += qtip_style

        button.setStyleSheet(custom_style_sheet)
        toolbar.addWidget(button)


    def update_button_names(self):
        # 最新の設定を取得
        config = mw.addonManager.getConfig(__name__)
        b_name, button_function_pairs = self.get_button_function_pairs(config)

        # ﾎﾞﾀﾝの名前を更新
        i = 0
        for action in self.toolBar.actions():
            button = self.toolBar.widgetForAction(action)
            if isinstance(button, QComboBox):
                self.toolBar.removeAction(action)
                self.make_combo_box(button_function_pairs)
                continue

            action.setText(b_name[i])
            button = self.toolBar.widgetForAction(action)
            button.setText(b_name[i])
            fm = QFontMetrics(button.font())
            width = fm.horizontalAdvance(b_name[i])
            button.setFixedSize(width + 10, 25)
            i += 1
    # ---------------------------------------------------


    def more_function(self, set_text, search_text=None):
        if search_text is not None: # ﾃｷｽﾄがすでに指定されている場合
            self.set_last_text(search_text)

            if (hasattr(mw, 'reviewer') and hasattr(mw.reviewer, 'card')
                and hasattr(mw.reviewer.card, 'note')):
                self.last_card_note = mw.reviewer.card.note() # ﾚﾋﾞｭﾜｰから取得

        if self.last_text is not None:
            config = mw.addonManager.getConfig(__name__)
            more_info = config[set_text]
            more_info = random.choice(more_info)

            body_has_card_context = (
                "{}" in more_info
                or self.template_has_card_field_placeholder(more_info, self.last_card_note)
            )

            prompt_text = self.build_prompt_text(
                prompt_template=more_info,
                fallback_text=self.last_text,
                note=self.last_card_note,
                prepend_fallback_if_no_placeholder=False,
            )
            self.handle_load_finished(
                prompt_text=prompt_text,
                click=True,
                fallback_text=self.last_text,
                body_has_card_context=body_has_card_context,
            )


    def wrap_with_quotes(self,text):
        return "'" + text + "'"


    def explain_with_ankiteminator(self, selected):
        print(selected)
        if not selected:
            return
        config = mw.addonManager.getConfig(__name__)
        default_prompt = config.get("default_prompt", "random_prompt")
        if default_prompt not in config:
            default_prompt = "random_prompt"
        self.more_function(default_prompt, selected)
        print("done")

    def contextMenu(self, webview: AnkiWebView, menu: QMenu,*args,**kwargs):
        selected = webview.page().selectedText()
        if not selected:
            return
        menu.addSeparator()
        self.context_action = QAction("🤖Explain with AnkiTerminator", mw)


        self.context_action.triggered.connect(
            lambda _, selected=selected: self.explain_with_ankiteminator(selected))

        menu.addAction(self.context_action)


    #MARK:show answer
    def show_answer_preload(self, card:Card=None, *args, **kwargs):
        try:
            is_same_card = False
            if self.previous_answer_card_id == card.id:
                is_same_card = True
            self.previous_answer_card_id = card.id
            if is_same_card:
                return

        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")

        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        submit = config["submit_text"]
        if not hide or not submit:
            self.load_and_interact(card, *args, **kwargs)

    #MARK:show question
    def show_question_preload(self, card:Card=None, *args, **kwargs):
        try:
            is_same_card = False
            if self.previous_question_card_id == card.id:
                is_same_card = True
            self.previous_question_card_id = card.id
            if is_same_card:
                return

        except Exception as e:
            print(f"[{ADDON_NAME}] Error: {e}")


        config = mw.addonManager.getConfig(__name__)
        hide = config["hide_the_sidebar_on_the_answer_screen"]
        submit = config["submit_text"]
        if hide and submit:
            self.load_and_interact(card, *args, **kwargs)


    def load_and_interact(self, card:Card=None, *args, **kwargs):
        # ﾄﾞｯｸﾞが非表示にされていたらGuiHooksを実行しない
        if not self.isVisible():
            return

        # 特定のﾉｰﾄﾀｲﾌﾟで2回呼び出される場合があるので1秒に制限
        current_time = time.time()
        if current_time - self.last_call < 1:
            return
        self.last_call = current_time

        config = mw.addonManager.getConfig(__name__)

        # text = mw.reviewer.card.note()["Front"] + selected_prompt

        if card is None and self.last_card is not None:# 手動で2回目の呼び出し
            card = self.last_card
        if card is None and self.last_card is None:
            return

        self.last_card = card
        note = card.note()
        self.last_card_note = note
        note_type = note.note_type()

        # 特定のﾉｰﾄﾀｲﾌﾟを除外
        if self.is_excluded_note_type(config, note_type):
            return

        first_field_name = self.get_priority_field_name(config, note_type)

        default_prompt = config.get("default_prompt", "random_prompt")
        if default_prompt not in config:
            default_prompt = "random_prompt"
        random_prompt = config[default_prompt]

        selected_prompt = random.choice(random_prompt)


        note_field_text = card.note()[first_field_name]
        self.set_last_text(note_field_text)

        body_has_card_context = (
            "{}" in selected_prompt
            or self.template_has_card_field_placeholder(selected_prompt, note)
        )

        prompt_text = self.build_prompt_text(
            prompt_template=selected_prompt,
            fallback_text=note_field_text,
            note=note,
            prepend_fallback_if_no_placeholder=False,
        )
        self.handle_load_finished(
            prompt_text=prompt_text,
            fallback_text=note_field_text,
            body_has_card_context=body_has_card_context,
        )

    # ------------------------------------------------


    def is_excluded_note_type(self, config, note_type):
        exclusion_list = config["exclusion_list"]
        # 特定のﾉｰﾄﾀｲﾌﾟを除外
        note_type_name = note_type['name']
        for exclusion in exclusion_list:
            if not exclusion or exclusion.isspace():
                continue
            if exclusion in note_type_name:
                return True
        return False

    def get_priority_field_name(self, config, note_type):
        Priority_Fields_list = config["Priority_Fields_list"]
        field_names = note_type['flds']
        first_field_name = field_names[0]['name']
        for field in field_names:
            if field['name'] in Priority_Fields_list:
                first_field_name = field['name']
                break
        return first_field_name

    def get_note_field_map(self, note):
        if note is None:
            return {}, {}

        field_map = {}
        try:
            note_type = note.note_type()
            for field in note_type.get('flds', []):
                field_name = field.get('name')
                if not field_name:
                    continue
                field_map[field_name] = note[field_name]
        except Exception:
            return {}, {}

        lower_field_map = {name.lower(): value for name, value in field_map.items()}
        return field_map, lower_field_map

    def template_has_card_field_placeholder(self, prompt_template: str, note=None):
        if not prompt_template:
            return False

        field_map, lower_field_map = self.get_note_field_map(note)
        if not field_map:
            return False

        placeholders = re.findall(r"\{([^{}]+)\}", prompt_template)
        for placeholder in placeholders:
            field_name_candidates = [name.strip() for name in placeholder.split("|") if name.strip()]
            for field_name in field_name_candidates:
                if field_name in field_map or field_name.lower() in lower_field_map:
                    return True

        return False

    def build_prompt_text(
        self,
        prompt_template: str,
        fallback_text: str = "",
        note=None,
        prepend_fallback_if_no_placeholder: bool = True,
    ):
        has_legacy_placeholder = "{}" in prompt_template
        has_named_placeholder = bool(re.search(r"\{[^{}]+\}", prompt_template))

        field_map, lower_field_map = self.get_note_field_map(note)
        prompt_text = prompt_template

        if has_legacy_placeholder:
            prompt_text = prompt_text.replace("{}", "'" + fallback_text + "'")

        def replace_named_placeholder(match):
            field_name_candidates = [name.strip() for name in match.group(1).split("|") if name.strip()]
            for field_name in field_name_candidates:
                if field_name in field_map:
                    return field_map[field_name]

                lower_field_name = field_name.lower()
                if lower_field_name in lower_field_map:
                    return lower_field_map[lower_field_name]

            return match.group(0)

        prompt_text = re.sub(r"\{([^{}]+)\}", replace_named_placeholder, prompt_text)

        if has_legacy_placeholder or has_named_placeholder:
            return prompt_text

        if prepend_fallback_if_no_placeholder:
            return fallback_text + prompt_text

        return prompt_text

    def get_priority_tag(self, config):
        Priority_tag_list = config["Priority_tag_list"]
        if self.last_card_note is not None:
            note = self.last_card_note # 引数から直接でないとｽﾞﾚるかも知らん
            tags = note.tags
            priority_tag = ""
            for tag in tags:
                for priority_tag_item in Priority_tag_list:
                    if priority_tag_item in tag:
                        priority_tag = priority_tag_item
                        break
                if priority_tag:
                    break
            return priority_tag
        else:
            priority_tag = ""

    # ------------------------------------------------

    # 送信ﾎﾞﾀﾝを押しても実行されないのでこれを参考にした
    # https://stackoverflow.com/questions/57879322/how-can-i-enter-data-into-a-custom-handled-input-field/57900849#57900849
            # BingChatはﾃｷｽﾄの入力すらもできません¯\_(ﾂ)_/¯
            # URLでｱｸｾｽすればいけるかも知らん(でもﾛｰﾄﾞが長い)

    ### clip bord ###
    def restore_clipboard(self):
        if isinstance(self.original_clipboard_data, QMimeData):
            self.clipboard.clear()
            self.clipboard.setMimeData(self.original_clipboard_data, QClipboard.Mode.Clipboard)
            self.original_clipboard_data = None

    def paste_from_clipboard(self):
        print("> run paste_from_clipboard")
        if self.auto_send_prompt_text:
            if self.auto_send_prompt_text == self.clipboard.text():
                self.webview.triggerPageAction(QWebEnginePage.WebAction.Paste)
                self.auto_send_prompt_text = None
                print("> paste done")
            else:
                print("!None prompt")

    def webaction_select_all(self):
        print("> run webaction_select_all")
        if self.auto_send_prompt_text:
            if self.auto_send_prompt_text == self.clipboard.text():
                self.webview.triggerPageAction(QWebEnginePage.WebAction.SelectAll)
                print("> SelectAll")



    ### send prompt ###
    def handle_load_finished(
        self,
        prompt_text: str,
        click=False,
        fallback_text: str = "",
        body_has_card_context: bool = False,
    ):
        config = mw.addonManager.getConfig(__name__)

        if not (config["submit_text"] or click):
            return

        no_auto_press_send_button = config.get("no_auto_press_send_button", False)
        prefix_has_card_context = False

        if config["change_Language"]:
            random_prompt_lang = config["language"]
            selected_prompt_lang = random.choice(random_prompt_lang)
            lang = shige_tr.lang
            print(lang)

            if self.template_has_card_field_placeholder(selected_prompt_lang, self.last_card_note):
                prefix_has_card_context = True

            selected_prompt_lang = self.build_prompt_text(
                prompt_template=selected_prompt_lang,
                fallback_text=lang if lang else "",
                note=self.last_card_note,
                prepend_fallback_if_no_placeholder=False,
            )
            prompt_text  = prompt_text + " " + selected_prompt_lang

        if config["is_i_am_studying"]:
            random_i_am_studying = config["i_am_studying"]
            selected_prompt_study = random.choice(random_i_am_studying)
            study_tag = self.get_priority_tag(config)

            if self.template_has_card_field_placeholder(selected_prompt_study, self.last_card_note):
                prefix_has_card_context = True

            selected_prompt_study = self.build_prompt_text(
                prompt_template=selected_prompt_study,
                fallback_text=study_tag if study_tag else "",
                note=self.last_card_note,
                prepend_fallback_if_no_placeholder=False,
            )
            prompt_text  = selected_prompt_study + " " + prompt_text

        if fallback_text and not body_has_card_context and not prefix_has_card_context:
            prompt_text = fallback_text + prompt_text

        now_AI_type = config["now_AI_type"]


        #📍use V2
        list_use_auto_prompt_v2 = [
            GOOGLE_BARD,
            BING_CHAT,
            PERPLEXITY,
            GOOGLE_AI_MODE
            ]


        if not now_AI_type in list_use_auto_prompt_v2:
            prompt_text = prompt_text.replace("'", "\\'")
            prompt_text = prompt_text.replace('"', '\\"')
            prompt_text = prompt_text.replace('\n', '\\n')
            prompt_text = prompt_text.replace('\r', '\\n')

        # skip_response_icon_check = "true"

        parent_element = ""

        # use v1

        if now_AI_type == CHAT_GPT:
            class_name = "#prompt-textarea"
            button_class = 'button[data-testid="send-button"]'
            stop_button_class = 'button[data-testid="stop-button"]'
            parent_element = ""

        elif now_AI_type == GROK_AI: #🚀
            class_name = '.tiptap.ProseMirror' #".query-bar textarea"
            button_class = 'button[type="submit"]' #'.f6d670'
            stop_button_class = 'button[type="submit"]' #''.f6d670' #'.f286936b'
            parent_element = ""

        elif now_AI_type == DUCK_AI: #🦆
            class_name = 'textarea[name="user-prompt"]'
            button_class = 'button[type="submit"].OBhZtIxa9q5aVP29xT9j'
            stop_button_class = 'button[type="submit"].YwVAQQko8KMb8FFwqGMD'
            parent_element = ""

        elif now_AI_type == DEEP_SEEK: #🐋
            class_name = "textarea._27c9245" #"#chat-input" #".c92459f0"
            button_class = '._52c986b' #'._7436101' #'._17e543b._7436101' #'._6f28693' #'.f6d670'
            stop_button_class = '' #'._17e543b._7436101'  #'._6f28693' #''.f6d670' #'.f286936b'
            stop_button_class = ''
            parent_element = ""

        elif now_AI_type == CLAUDE:
            class_name = '.ProseMirror'
            button_class = 'button[aria-label="Send message"]' #'button[aria-label="Send Message"]'
            stop_button_class = 'button[aria-label="Stop response"]' #'button[aria-label="Stop Response"]'
            parent_element = ""

        elif now_AI_type == IMAGE_FX:
            class_name = '[role="textbox"]'
            button_class = '.sc-6eb6c34b-1'
            stop_button_class = ''
            parent_element = ""


        # use v2
        elif now_AI_type == PERPLEXITY:
            class_name = "#ask-input"
            button_class = 'button[aria-label="Submit"]'
            stop_button_class = "" #'button.bg-offsetPlus'
            parent_element = ""

        elif now_AI_type == GOOGLE_BARD:
            class_name = ".textarea.new-input-ui" #".ql-editor.textarea"
            button_class = '.send-button.submit' #".send-button"
            stop_button_class = '.send-button.stop' #".send-button"
            parent_element = ""

        elif now_AI_type == BING_CHAT:
            class_name = "#userInput"
            button_class = '[data-testid="submit-button"]'
            stop_button_class = ""

        elif now_AI_type == GOOGLE_AI_MODE:
            class_name = "textarea.ITIRGe"
            button_class = 'button[data-xid="input-plate-send-button"]'
            stop_button_class = ""

        else:
            return


        if no_auto_press_send_button:
            stop_button_class = ""
            button_class = ""


        if now_AI_type in list_use_auto_prompt_v2:
            # use v2 click
            self.auto_click_v2(stop_button_class, class_name, prompt_text, button_class)
            return

        # use v1 click

        js_code = f"""

        function replaceValue(selector, value) {{
        const el = document.querySelector(selector);
        if (el) {{
            el.focus();
            document.execCommand('selectAll');
            if (!document.execCommand('insertText', false, value)) {{
            el.value = '{prompt_text}';
            }}
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            var inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
            el.dispatchEvent(inputEvent);
        }}
        return el;
        }}
        replaceValue('{class_name}', '{prompt_text}');
        """

        if stop_button_class:
            js_code += f"""
            setTimeout(function() {{
                var button = document.querySelector('{stop_button_class}'){parent_element};
                if (button) {{
                    button.click();
                }}
            }}, 100);
            """

        if button_class:
            js_code += f"""
        setTimeout(function() {{
            var submitButton = document.querySelector('{button_class}');
            if (submitButton && !submitButton.disabled && submitButton.getAttribute('aria-disabled') !== 'true') {{
                submitButton.click();
            }}
        }}, 200);
        """

        self.webview.page().runJavaScript(js_code, self.js_callback)


    def js_callback(self, result):
        pass
        # print(f"[DEBUG] JavaScript result: {result}")



    #MARK:auto_click_v2

    def auto_click_v2(self, stop_button_class, class_name, prompt_text, button_class):
        FOCUS_SELECT_DELAY = 100
        SELECT_ALL_DELAY = 400
        PASTE_DELAY = 500
        SUBMIT_BUTTON_DELAY = 600
        RESTORE_CLIPBOARD_DELAY = 700

        # self.webview.triggerPageAction(QWebEnginePage.WebAction.Unselect)
        # https://stackoverflow.com/a/8380837

        if stop_button_class:
            js_code = f"""
            function clickButton() {{
                var button = document.querySelector('{stop_button_class}');
                if (button && !button.disabled && button.getAttribute('aria-disabled') !== 'true') {{
                    button.click();
                }}
            }}
            clickButton();
            """
            self.webview.page().runJavaScript(js_code, self.js_callback_v2_click)

        if self.focus_text_area_js:
            js_code = self.focus_text_area_js
        else:
            path_focus_text_area_js = join(dirname(__file__), "focus_text_area.js")
            with open(path_focus_text_area_js, 'r', encoding='utf-8') as f:
                self.focus_text_area_js = f.read()
                js_code = self.focus_text_area_js

        js_code = js_code.replace('__PLACEHOLDER_SELECTOR__', f"{class_name}")
        js_code = js_code.replace('__PLACEHOLDER_DELAY__', f"{FOCUS_SELECT_DELAY}")

        self.clipboard = mw.app.clipboard()
        original_data = self.clipboard.mimeData(QClipboard.Mode.Clipboard)
        self.original_clipboard_data = QMimeData()

        for format in original_data.formats():
            self.original_clipboard_data.setData(format, original_data.data(format))

        print(f"[{ADDON_NAME}] prompt_text:", prompt_text)

        self.clipboard.clear()
        self.clipboard.setText(prompt_text)
        self.auto_send_prompt_text = prompt_text

        QTimer.singleShot(SELECT_ALL_DELAY, self.webaction_select_all)
        QTimer.singleShot(PASTE_DELAY, self.paste_from_clipboard)

        # submit
        if button_class:
            js_code += f"""
            setTimeout(function() {{

                var buttons = document.querySelectorAll('{button_class}');
                var targetButton = null;

                for (var i = 0; i < buttons.length; i++) {{
                    var button = buttons[i];
                    var style = window.getComputedStyle(button);
                    var isVisible = style.display !== 'none' && button.offsetParent !== null && style.pointerEvents !== 'none';

                    if (isVisible) {{
                        targetButton = button;
                        break;
                    }}
                }}

                if (targetButton && !targetButton.disabled && targetButton.getAttribute('aria-disabled') !== 'true') {{
                    try {{
                        targetButton.click();
                    }} catch (e) {{
                    }}
                }}
            }}, {SUBMIT_BUTTON_DELAY});
            """

        self.webview.page().runJavaScript(js_code, self.js_callback_v2_click)

        QTimer.singleShot(RESTORE_CLIPBOARD_DELAY, self.restore_clipboard)


    def js_callback_v2_click(self, result):
        print(f"[DEBUG] JavaScript result: {result}")





chatGPTdockWidget = None #type: QDockWidget
dock_content = None #type: ResizableWebView

#MARK:check dock pos
def check_dock_widget_position():
    if not isinstance(chatGPTdockWidget, QDockWidget):
        return
    dock_widgets = mw.findChildren(QDockWidget)
    widget_found = False
    for widget in dock_widgets:
        if widget.objectName() == "AnkiTerminator_dock":
            widget_found = True
            current_area = mw.dockWidgetArea(widget)
            if current_area != Qt.DockWidgetArea.RightDockWidgetArea:
                mw.removeDockWidget(widget)
                mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, widget)
            break
    if not widget_found:
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, chatGPTdockWidget)


#MARK:web view
def Web_view(name, url):
    global chatGPTdockWidget
    global dock_content
    global web_shortcut

    if chatGPTdockWidget is not None:
        if chatGPTdockWidget.isVisible():
            chatGPTdockWidget.hide()
            mw.web.setFocus()
        else:
            chatGPTdockWidget.show()
            chatGPTdockWidget.setFocus()
            check_dock_widget_position()
            dock_content.get_field_text()
        return


    mw.anki_Terminator_dock_content = dock_content = ResizableWebView(name, url)
    mw.anki_Terminator_chatGPTdockWidget = chatGPTdockWidget = QDockWidget()

    chatGPTdockWidget.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
    chatGPTdockWidget.setTitleBarWidget(QWidget()) # ﾀｲﾄﾙﾊﾞｰを空のｳｨｼﾞｪｯﾄに置き換え

    chatGPTdockWidget.setObjectName("AnkiTerminator_dock")
    # chatGPTdockWidget.setWindowTitle("AnkiTerminator")
    chatGPTdockWidget.setWidget(dock_content)
    QTimer.singleShot(0, lambda: mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, chatGPTdockWidget))

    QTimer.singleShot(500, check_dock_widget_position)

    config = mw.addonManager.getConfig(__name__)
    Enter_Short_cut_Key = config["Enter_Short_cut_Key"]


    def send_shortcut():
        print("send_shortcut")
        config = mw.addonManager.getConfig(__name__)
        now_AI_type = config["now_AI_type"]
        if now_AI_type == CHAT_GPT:
            button_class = 'button[data-testid="send-button"]'
        elif now_AI_type == GOOGLE_BARD:
            button_class = ".send-button"
        else:
            return
        js_code = f"""
        setTimeout(function() {{
            var submitButton = document.querySelector('{button_class}');
            if (submitButton) {{
                submitButton.click();
            }}
        }}, 200);
        """
        dock_content.webview.page().runJavaScript(js_code, dock_content.js_callback)

    menu = QAction("Send Prompt", mw)
    menu.triggered.connect(send_shortcut)

    from .make_manu import get_anki_terminator_menu
    get_anki_terminator_menu().addAction(menu)

    menu.setShortcut(QKeySequence(Enter_Short_cut_Key))
    web_shortcut = menu

    make_close_menu_action()


#MARK:close memu
def make_close_menu_action():
    global completely_close_sidebar
    completely_close_sidebar = QAction("Completely close Sidebar (for update add-on)", mw)
    completely_close_sidebar.triggered.connect(close_all_dock_widget)
    from .make_manu import get_anki_terminator_menu
    get_anki_terminator_menu().addAction(completely_close_sidebar)


#📍use config
#MARK:close sidebar
def close_all_dock_widget(*args, **kwargs):
    global chatGPTdockWidget
    global dock_content
    global web_shortcut
    global completely_close_sidebar

    try:
        for dialog in list_new_dialogs[:]:
            if isinstance(dialog, QWidget):
                try:
                    dialog.close()
                    dialog.deleteLater()
                except Exception as e:
                    print(f"[{ADDON_NAME}] Error: {e}")
        list_new_dialogs.clear()
        mw.AnkiTerminator_new_dialog = None
    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e} ")

    if isinstance(chatGPTdockWidget, QDockWidget):
        if isinstance(dock_content, ResizableWebView):

            if hasattr(dock_content, "webview") and dock_content.webview.page():
                page = dock_content.webview.page()
                dock_content.webview.setPage(None)
                page.deleteLater()

            dock_content.remove_all_hooks()
            dock_content.close()
            dock_content.deleteLater()
            dock_content = None

        chatGPTdockWidget.close()
        chatGPTdockWidget.deleteLater()
        chatGPTdockWidget = None

    if hasattr(mw, "AnkiTerminator_image_Ai_dialog"):
        AI_image_widet = mw.AnkiTerminator_image_Ai_dialog
        if isinstance(AI_image_widet, QWidget):
            AI_image_widet.close()
            AI_image_widet.deleteLater()
            mw.AnkiTerminator_image_Ai_dialog = None

    from .make_manu import get_anki_terminator_menu

    if web_shortcut:
        get_anki_terminator_menu().removeAction(web_shortcut)
        web_shortcut = None

    if completely_close_sidebar:
        get_anki_terminator_menu().removeAction(completely_close_sidebar)
        completely_close_sidebar = None

gui_hooks.addons_dialog_will_show.append(close_all_dock_widget)


#MARK:wrap
try:
    from anki.hooks import wrap
    from aqt.addons import ChooseAddonsToUpdateDialog

    def addons_to_update_dialog_did_show(*args, **kawargs):
        close_all_dock_widget()
        print(f"[{ADDON_NAME}] >>> on close_all_dock_widget")

    ChooseAddonsToUpdateDialog.ask = wrap(
        ChooseAddonsToUpdateDialog.ask, addons_to_update_dialog_did_show)

    #🚨ChooseAddonsToUpdateDialog以外からｻｲﾄﾞﾊﾞｰを閉じるとAnkiがｸﾗｯｼｭするﾘｽｸがある(V1が壊れた原因)

except Exception as e:
    print(f"[{ADDON_NAME}] Error: {e}")


#MARK:BGM

from .config.BGM_player import pyg_play_sound

def get_path(name):
    addon_path = dirname(__file__)
    parentFoldere = SOUND_SYSTEM
    config_folder = CONFIG_FOLDER
    audio_folder = join(addon_path,config_folder,parentFoldere, name)
    return audio_folder

def PYGsound(sound_name,volume=None):
    config = mw.addonManager.getConfig(__name__)
    if not volume == None:
        EffectVolume = volume
    else:
        EffectVolume = config["EffectVolume"]
    pyg_play_sound(get_path(sound_name), EffectVolume,False,True)




# 🚨
# from aqt.utils import tooltip
# def close_dock_widget(addonmanager, name, *args, **kwargs):
#     if name == __name__.split(".")[0]:
#         global chatGPTdockWidget
#         global dock_content
#         global web_shortcut
#         if isinstance(chatGPTdockWidget, QDockWidget):
#             tooltip("")

# gui_hooks.addon_manager_did_install_addon.append(close_dock_widget)
# gui_hooks.addons_dialog_will_delete_addons.append(close_dock_widget)
# gui_hooks.addons_dialog_will_delete_addons.append(close_dock_widget)


# 🚨 add-onの更新時にAnkiがｸﾗｯｼｭするﾊﾞｸﾞがある
    # def close_cookie_profile(self):

    #     if hasattr(self, 'webview'):
    #         if self.webview.page():
    #             page = self.webview.page()
    #             self.webview.setPage(None)
    #             page.deleteLater()
    #             # del page
    #         # del self.webview
    #         self.webview.deleteLater()
    #         self.webview = None

    #     if hasattr(self, 'webpage'):
    #         # del self.webpage
    #         self.webpage.deleteLater()
    #         self.webpage = None

    #     QCoreApplication.processEvents()

    #     self.cookie_profile.setPersistentStoragePath("")
    #     self.cookie_profile.setPersistentCookiesPolicy(
    #         QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)

    #     referrers = gc.get_referrers(self.cookie_profile)
    #     if len(referrers) == 1:  # 参照がselfのみ
    #         # deleteLaterだと削除されない
    #         # webviewが削除されるにdelするとｸﾗｯｼｭする
    #         del self.cookie_profile
    #         self.cookie_profile = None


# 🚨 add-onの更新時にAnkiがｸﾗｯｼｭするﾊﾞｸﾞがある
# def close_dock_widget(addonmanager, name, *args, **kwargs):
#     if name == __name__.split(".")[0]:

#         def delayed_close():
#             global chatGPTdockWidget
#             global dock_content
#             if isinstance(chatGPTdockWidget, QDockWidget):
#                 if isinstance(dock_content, ResizableWebView):
#                     dock_content.close_cookie_profile()
#                     dock_content.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
#                     dock_content.close()
#                     dock_content.deleteLater()
#                     dock_content = None

#                 chatGPTdockWidget.close()
#                 chatGPTdockWidget.deleteLater()
#                 chatGPTdockWidget = None

#                 QCoreApplication.processEvents()

#             loop = QEventLoop()
#             QTimer.singleShot(1000, loop.quit)
#             loop.exec()
#             QCoreApplication.processEvents()


#         QTimer.singleShot(0, delayed_close)



# 🚨 add-onの更新時にAnkiがｸﾗｯｼｭするﾊﾞｸﾞがある
# gui_hooks.addon_manager_will_install_addon.remove(close_dock_widget)
# gui_hooks.addon_manager_will_install_addon.append(close_dock_widget)

