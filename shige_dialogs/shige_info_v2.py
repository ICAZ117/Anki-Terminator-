# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

from os.path import join, dirname
from typing import Literal

from aqt import QWidget

if __name__ == "__main__":
    from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QDialog
    from PyQt6.QtGui import QPixmap, QIcon, QResizeEvent
    from PyQt6.QtCore import QTimer
else:
    from aqt.qt import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QDialog
    from aqt.qt import QPixmap, QIcon, QResizeEvent
    from aqt.qt import QTimer

from ..path_manager import ADDON_NAME


POPUP_ICON = "popup_icon.png"

POPUP_DEFAULT = "popup_shige.png"
POPUP_QUESTION = "popup_shige_question.png"
POPUP_INFO = "popup_shige_info.png"
POPUP_INFO_02 = "popup_shige_info_02.png"
POPUP_WARNING = "popup_shige_warning.png"


def get_icon_path(name, format="icon"):
    addon_path = dirname(__file__)
    icon_path = join(addon_path, name)

    if format == "pix":
        return QPixmap(icon_path)
    else:
        return QIcon(icon_path)


class ShigeInfo(QDialog):
    def __init__(
        self,
        text: str,
        parent: None = None,
        help: None = None,
        type: Literal["info", "warning", "critical", "question", "lightbulb", "notice"] = "info",
        title: str = ADDON_NAME,
        textFormat: None = None,
        customBtns: None = None,
    ):
        super().__init__(parent)
        self.response = False

        if type == "warning":
            icon = QPixmap(get_icon_path(POPUP_INFO, "pix"))
        elif type == "critical":
            icon = QPixmap(get_icon_path(POPUP_WARNING, "pix"))
        elif type == "question":
            icon = QPixmap(get_icon_path(POPUP_QUESTION, "pix"))
        elif type == "lightbulb":
            icon = QPixmap(get_icon_path(POPUP_DEFAULT,"pix"))
        elif type == "notice":
            icon = QPixmap(get_icon_path(POPUP_INFO_02,"pix"))
        else:
            icon = QPixmap(get_icon_path(POPUP_DEFAULT, "pix"))

        icon_label = QLabel()
        icon_label.setPixmap(icon)

        text_edit = QTextBrowser()
        text_edit.setReadOnly(True)
        text_edit.setOpenExternalLinks(True)

        if "<img src=" in text:
            textFormat = "rich"
            text.replace("\n","<br>")

        if textFormat == "plain":
            text_edit.setPlainText(text)
        elif textFormat == "rich":
            text_edit.setHtml("<html><body>" + text + "</body></html>")
        elif textFormat == "markdown":
            text_edit.setHtml("<html><body><pre>" + text + "</pre></body></html>")
        else:
            text_edit.setPlainText(text)

        self.main_layout = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(icon_label)
        hbox.addWidget(text_edit)

        self.main_layout.addLayout(hbox)

        if customBtns:
            if customBtns:
                btn_layout = QHBoxLayout()
                btn_layout.addStretch(1)
                for btn in customBtns:
                    btn : QPushButton
                    btn_layout.addWidget(btn)
                    # btn.clicked.connect(self.accept)
                self.main_layout.addLayout(btn_layout)
        else:
            btn = QPushButton("OK")
            btn.setFixedWidth(100)
            btn.clicked.connect(self.accept)

            btn_layout = QHBoxLayout()
            btn_layout.addStretch(1)
            btn_layout.addWidget(btn)

            self.main_layout.addLayout(btn_layout)

        self.setLayout(self.main_layout)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(get_icon_path(POPUP_ICON)))

        # def get_content_height():
        #     # content_height = int(text_edit.document().size().height() +100)
        #     content_height = int(text_edit.document().size().height() +50)
        #     self.resize(400, content_height if content_height < 400 else 400)

        # QTimer.singleShot(0, get_content_height)

    def run_excec(self):
        if hasattr(self, "exec"):
            self.exec()
        else:
            self.exec_()

        # self.show()

    @staticmethod
    def question(parent, text, yes_text="OK", no_text="Cancel", width=None, height=None, extra_func=None, timeout_seconds=20):
        yes_button = QPushButton(yes_text)
        no_button = QPushButton(no_text)
        dialog = ShigeInfo(text, parent, type="question", customBtns=[yes_button, no_button])

        if extra_func and isinstance(extra_func, QWidget):
            dialog.main_layout.addWidget(extra_func)

        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)

        def on_yes():
            timeout_timer.stop()
            dialog.response = True
            dialog.accept()

        def on_no():
            timeout_timer.stop()
            dialog.response = False
            dialog.reject()

        def on_timeout():
            on_no()

        yes_button.clicked.connect(on_yes)
        no_button.clicked.connect(on_no)
        timeout_timer.timeout.connect(on_timeout)

        if width is not None and height is not None:
            dialog.resize(width, height)

        timeout_timer.start(timeout_seconds * 1000)

        dialog.run_excec()
        return dialog.response


    def resizeEvent(self, event:"QResizeEvent"):
        size = event.size()
        print(f"Width: {size.width()}, Height: {size.height()}")
        super().resizeEvent(event)



# e.g.
# from .shige_dialogs.shige_info import ShigeInfo
# result = ShigeInfo.question(
#     parent=None,
#     text=""" text """,
#     yes_text="OK",
#     no_text="Cancel",
#     width=547,
#     height=340,
# )
# if result:
#     print("Yes")
# else:
#     print("Cancel")


# if __name__ == "__main__":
#     import sys
#     from PyQt6.QtWidgets import QApplication

#     app = QApplication(sys.argv)

#     info_dialog_00 = ShigeInfo(text="warning", type="warning")
#     info_dialog_01 = ShigeInfo(text="critical", type="critical")
#     info_dialog_02 = ShigeInfo(text="question", type="question")
#     info_dialog_03 = ShigeInfo(text="lightbulb", type="lightbulb")
#     info_dialog_04 = ShigeInfo(text="notice", type="notice")

#     info_dialog_00.exec()
#     info_dialog_01.exec()
#     info_dialog_02.exec()
#     info_dialog_03.exec()
#     info_dialog_04.exec()


#     sys.exit(app.exec())