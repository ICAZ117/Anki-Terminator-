# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

from os.path import join, dirname

try:
    from PyQt6.QtWidgets import (
        QDialog, QHBoxLayout, QTabWidget, QWidget, QSizePolicy,
        QVBoxLayout, QLabel, QPushButton
    )
    from PyQt6.QtGui import QIcon, QResizeEvent, QPixmap
    from PyQt6.QtCore import QUrl, Qt
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
except:
    from aqt.qt import (
        QDialog, QHBoxLayout, QTabWidget, QWidget, QSizePolicy,
        QVBoxLayout, QLabel, QPushButton
    )
    from aqt.qt import QIcon, QResizeEvent, QPixmap
    from aqt.qt import QUrl, Qt
    from aqt.qt import QWebEngineView
    from aqt.qt import QWebEnginePage, QWebEngineSettings

from aqt import mw, gui_hooks
from aqt.utils import openLink

from .button_manager import mini_button
from .shige_addons import add_shige_addons_tab
from .endroll.endroll import add_credit_tab

from .change_log import OLD_CHANGE_LOG #🟢
from .patrons_list import PATRONS_LIST #🟢
from ..path_manager import ADDON_NAME

CHANGE_LOG_DEFAULT = ""
CHANGE_LOG = "is_change_log"
# CHANGE_LOG_DAY = "2025-09-29a"
CHANGE_LOG_DAY = "2026-02-15" #🟢

POKEBALL_PATH = r"popup_icon.png"

THE_ADDON_NAME = "🤖Anki Terminator (Created by Shige)" #🟢

REPORT_URL = "https://shigeyukey.github.io/shige-addons-wiki/AnkiTerminator/anki_terminator_00.html#report-a-problem-or-request"


# popup-size
# mini-pupup
SIZE_MINI_WIDTH = 577
SIZE_MINI_HEIGHT = 522
# Width: 577, Height: 522 #🟢

# Large-popup
SIZE_BIG_WIDTH = 700
SIZE_BIG_HEIGHT = 500

ANKI_WEB_URL = ""
RATE_THIS_URL = ""

ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__)
# ｱﾄﾞｵﾝのURLが数値であるか確認
if (isinstance(ADDON_PACKAGE, (int, float))
    or (isinstance(ADDON_PACKAGE, str)
    and ADDON_PACKAGE.isdigit())):
    ANKI_WEB_URL = f"https://ankiweb.net/shared/info/{ADDON_PACKAGE}"
    RATE_THIS_URL = f"https://ankiweb.net/shared/review/{ADDON_PACKAGE}"


PATREON_URL = "http://patreon.com/Shigeyuki"
REDDIT_URL = "https://www.reddit.com/r/Anki/comments/1b0eybn/simple_fix_of_broken_addons_for_the_latest_anki/"

POPUP_PNG = r"popup_shige.png"




patron_url_href = '<a href="https://www.patreon.com/posts/136548011" target="_blank">'

try:
    _patreon_addon_path = join(dirname(dirname(__file__)), "ankiarcade_thumbnail.webp")
    str_patreon_addon_path = (
        f'{patron_url_href}'
        f'<img src="{_patreon_addon_path}"></a>'
    )
except Exception as e:
    print(f"[{ADDON_NAME}] ")
    str_patreon_addon_path = ""




NEW_FEATURE = """
2026-04-29 Enhanced
- Added support for Google AI mode.
- Enhanced the Auto-Send V2 feature.
- Added auto save audio. (disabled by default)
- Added AdBlock. (disabled by default)
- Added a workaround for the update error. (subfolder)
- Optimized some code.

Note: Auto send is fragile, if it doesn't work please contact me.

[ New Features ]

[ Auto Save Audio ] This option is disabled by default. Auto saves audio played on websites or AI generated TTS and adds it to your cards. Some websites use special methods for audio playback, in such cases the add-on cannot save the audio.
Notes: Saving audio may be prohibited on some websites due to copyright protection or their terms of service, these vary by website and country. Even if downloads are permitted redistribution is often prohibited so please be careful not to share the deck’s audio in such cases. Please check whether downloading is permitted or not and use this feature at your own risk, if you have concerns I recommend not using this feature If you're looking for redistributable audio or a free batch generate solution I recommend my add-on PyperTTS (428593773).

[ AdBlock ] Simply blocks ads (I have not yet developed advanced features), this option is disabled by default (some websites may not display properly when using AdBlock) This AdBlock feature uses a wheel auto downloaded from an external source (python-adblock pip: https://pypi.org/project/adblock/  github: https://github.com/ArniDagur/python-adblock ), so if you have concerns I recommend not using this feature.

[ Enable or Disable Cookies ] I added an option to enable or disable saving cookies. If you disable cookies all existing cookie data will be auto deleted. If cookies are disabled restarting Anki will reset all login data (in other words this cookie feature is intended to reduce the inconvenience of re logging in) Cookies are encrypted by Chromium but Anki is open source and the add-ons are independently developed so this add-on does not have the robust security like Chrome or Edge developed by corporations. If you are concerned about security I recommend disabling this feature. (or avoid using important accounts)

( Subfolder ) Added a feature to auto generate subfolders and store some data there, this resolves a known bug that caused errors when updating or removing this add-on. This subfolder will appear as a new add-on in the add-ons dialog (to make it easier to delete manually. In short an add-on folder will be added and this is normal) If you try to delete this subfolder while the add-on is running an error will occur, so please disable AnkiTerminator, restart Anki, and then delete it. (or hold down the Shift key to launch Anki in Safe mode)
"""


UPDATE_TEXT = "I updated this Add-on."

SPECIAL_THANKS ="""\
[ Patreon ] Special thanks
Without the support of my Patrons, I would never have been
able to develop this. Thank you very much!🙏"""

# CHANGE_LOG_TEXT = """\
# [ Change log : {addon} ]
# Shigeyuki: Hi AI geek, thanks for using this add-on!ඞ {update_text}
# {new_feature}
# ---
# I'm looking for supporters for my add-ons development, because I like Anki! So far I fixed and customized 80+ discontinued add-ons and created 30+ new add-ons. If you support my volunteer development you will get 14 add-ons for patrons only and 15 game themes included in AnkiArcade. If you have any ideas or requests feel free to send them to me, thanks! :D

# [ Old change log ]
# {old_change_log}

# {special_thanks}

# {patron}

# """.format(addon=THE_ADDON_NAME,
#             update_text=UPDATE_TEXT,
#             new_feature=NEW_FEATURE,
#             old_change_log = OLD_CHANGE_LOG,
#             special_thanks=SPECIAL_THANKS,
#             patron=PATRONS_LIST)


CHANGE_LOG_TEXT = f"""\
[ Change log : {THE_ADDON_NAME} ]

Shigeyuki : Hi AI geek thanks for using this add-on!ඞ {UPDATE_TEXT}
{NEW_FEATURE}
--------
[ 🎮Shige's Gamification add-ons ] I develop as a hobby and so far I've fixed 80+ broken add-ons for free by request from users and released 30+ original add-ons for free! If you become a patron ($5/month) and support my volunteer development you can download the Patrons only add-on AnkiArcade.
{str_patreon_addon_path}
[ {patron_url_href}AnkiArcade (Patrons only)</a> ] AnkiArcade is a multi minigame Anki add-on that I am primarily developing. Aiming for quality comparable to indie games, it currently features 40+ animated pixel art characters, 400+ sound effects, 500+ BGM tracks, and 400+ pixel art enemy characters, progress bar, pomodoro timer, and more! If you become a Patron you can use it. (Not related to the official Anki.)
--------

[ Old change log ]
{OLD_CHANGE_LOG}

{SPECIAL_THANKS}

{PATRONS_LIST}
"""



CHANGE_LOG_TEXT_B = """\
Shigeyuki :
Hello, thank you for using this add-on, I'm Shige!😆

I development of Anki Add-ons for Gamification Learning
and so far I fixed 40+ broken add-ons.
If you like this add-on, please support my development on Patreon,
and you can get add-ons for patrons only(about 28 Contents).

If you have any problems or requests feel free to contact me.
Thanks!

[1] How to contact me
    - AnkiWeb (Rate Comment) : You can contact me anonymously.
    - Reddit (Fixed add-ons) : You can request me to repair broken Add-ons.
    - Github (Issues) : Makes it easier to track problems.
    - Patreon (DM) : Response will be prioritized.


----
{addon}
[ Change log ]

{new_feature}

{old_change_log}

----
{special_thanks}

{patron}
""".format(
            addon=THE_ADDON_NAME,
            patron=PATRONS_LIST,
            special_thanks=SPECIAL_THANKS,
            new_feature=NEW_FEATURE,
            old_change_log=OLD_CHANGE_LOG,
            )



# ------- Rate This PopUp ---------------

def set_gui_hook_change_log():
    gui_hooks.main_window_did_init.append(change_log_popup)
    # gui_hooks.main_window_did_init.append(add_config_button)

def change_log_popup(*args,**kwargs):
    try:
        config = mw.addonManager.getConfig(__name__)
        if (config.get(CHANGE_LOG, CHANGE_LOG_DEFAULT) != CHANGE_LOG_DAY):
            dialog = CustomDialog(mw, CHANGE_LOG_TEXT, size_mini=True)
            dialog.show()
            config[CHANGE_LOG] =  CHANGE_LOG_DAY
            mw.addonManager.writeConfig(__name__, config)
    except Exception as e:
        pass




def change_log_popup_B(*args,**kwargs):
    try:
        dialog = CustomDialog(mw, CHANGE_LOG_TEXT_B, True)
        dialog.show()
    except Exception as e:
        pass



# ----- add-onのconfigをｸﾘｯｸしたら設定ｳｨﾝﾄﾞｳを開く -----
def add_config_button():
    mw.addonManager.setConfigAction(__name__, change_log_popup_B)
    # ----- ﾒﾆｭｰﾊﾞｰに追加 -----🟢
    # action = QAction(THE_ADDON_NAME, mw)
    # qconnect(action.triggered, change_log_popup_B)
    # mw.form.menuTools.addAction(action)

# ================================================


def handle_new_window(url):
    openLink(url)

# gifｱﾆﾒを表示するためにQWebEngineを使う
class CustomWebEnginePage(QWebEnginePage):
    def createWindow(self, _type):
        new_page = CustomWebEnginePage(self)
        new_page.urlChanged.connect(handle_new_window)
        return new_page

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass


def build_change_log_html(change_log_text:str):

    escaped_text = change_log_text.replace("\n", "<br>")

    is_dark_mode = True
    try:
        from aqt.theme import theme_manager
        is_dark_mode = theme_manager.night_mode
    except Exception as e:
        print(f"[{ADDON_NAME}] Error: {e}")
        is_dark_mode = True

    if is_dark_mode:
        bg_color = "#2b2b2b"
        text_color = "#e0e0e0"
        link_color = "#64b5f6"
        visited_color = "#ba68c8"
        scrollbar_thumb = "rgba(120, 120, 120, 0.7)"
        scrollbar_track = "#1e1e1e"
    else:
        bg_color = "#ffffff"
        text_color = "#000000"
        link_color = "#0066cc"
        visited_color = "#7030a0"
        scrollbar_thumb = "rgba(150, 150, 150, 0.7)"
        scrollbar_track = "#f5f5f5"

    str_html =  f"""
<html>
<head>

<style>
body {{
    font-family: system-ui;
    font-size: 12px;
    background-color: {bg_color};
    color: {text_color};
    margin: 0;
    padding: 10px;
}}

a {{
    color: {link_color};
}}

a:visited {{
    color: {visited_color};
}}

a:hover {{
    text-decoration: underline;
}}

::-webkit-scrollbar {{
    width: 12px;
}}
::-webkit-scrollbar-track {{
    background: {scrollbar_track};
}}
::-webkit-scrollbar-thumb {{
    background-color: {scrollbar_thumb};
    border-radius: 6px;
    border: 2px solid transparent;
    background-clip: content-box;
}}
::-webkit-scrollbar-thumb:hover {{
    background-color: rgba(180, 180, 180, 0.9);
}}

</style>
    </head>
    <body>
        <div style="white-space: pre-wrap;">{escaped_text}</div>
    </body>
</html>
"""
    return str_html





class CustomDialog(QDialog):
    def __init__(self, parent=None, change_log_text=CHANGE_LOG_TEXT, more_button=False, size_mini=False):
        super().__init__(parent)
        try:
            addon_path = dirname(__file__)
            icon = QPixmap(join(addon_path, POPUP_PNG))

            if size_mini:
                self.resize(SIZE_MINI_WIDTH, SIZE_MINI_HEIGHT)
            else:
                self.resize(SIZE_BIG_WIDTH, SIZE_BIG_HEIGHT)

            pokeball_icon = QIcon(join(addon_path, POKEBALL_PATH))
            self.setWindowIcon(pokeball_icon)

            self.setWindowTitle(THE_ADDON_NAME)

            tab_widget = QTabWidget()
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            icon_label = QLabel()
            icon_label.setPixmap(icon)

            hbox = QHBoxLayout()

            change_log_label = QWebEngineView(tab)
            change_log_label.setPage(CustomWebEnginePage(change_log_label))
            change_log_label.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
            )
            change_log_label.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            change_log_label.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, True
            )
            change_log_label.setHtml(
                build_change_log_html(change_log_text),
                baseUrl=QUrl.fromLocalFile(addon_path + "/"),
            )
            change_log_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


            hbox.addWidget(icon_label)
            hbox.addWidget(change_log_label)

            tab_layout.addLayout(hbox)

            button_layout = QHBoxLayout()
            button_layout.addStretch()

            self.yes_button = QPushButton("💖Become a Patron")
            self.yes_button.clicked.connect(lambda: openLink(PATREON_URL))
            self.yes_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            mini_button(self.yes_button)

            self.report_button = QPushButton("🚨Report")
            self.report_button.clicked.connect(lambda: openLink(REPORT_URL))
            self.report_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            mini_button(self.report_button)

            self.no_button = QPushButton("OK (Close)")
            self.no_button.clicked.connect(self.close)
            self.no_button.setFixedWidth(120)

            button_layout.addWidget(self.yes_button)
            button_layout.addWidget(self.report_button)
            button_layout.addWidget(self.no_button)

            tab_widget.addTab(tab, "Change Log")
            add_credit_tab(self, tab_widget)
            add_shige_addons_tab(self, tab_widget)

            main_layout = QVBoxLayout(self)
            main_layout.addWidget(tab_widget)
            main_layout.addLayout(button_layout)

            self.setLayout(main_layout)

        except Exception as e:
            print(f"[{ADDON_NAME}] Erorr: {e} ")

    def resizeEvent(self, event:"QResizeEvent"):
        size = event.size()
        print(f"Width: {size.width()}, Height: {size.height()}")
        super().resizeEvent(event)
