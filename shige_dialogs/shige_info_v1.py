from os.path import join, dirname
from typing import Literal

from aqt import (QHBoxLayout, QLabel, QPixmap, QPushButton,
                QTextBrowser, QTimer, QVBoxLayout, QIcon, QDialog)

# from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QTextBrowser,
#                             QVBoxLayout, QDialog)
# from PyQt6.QtGui import QPixmap, QIcon
# from PyQt6.QtCore import QTimer

from ..._version import ADDON_NAME


POPUP_ICON = "popup_icon.png"

POPUP_DEFAULT = "popup_shige.png"
POPUP_QUESTION = "popup_shige_question.png"
POPUP_INFO = "popup_shige_info.png"
POPUP_INFO_02 = "popup_shige_info_02.png"
POPUP_WARNING = "popup_shige_warning.png"


def get_icon_path(name, format="icon"):
    """ pix,icon """
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

        layout = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(icon_label)
        hbox.addWidget(text_edit)

        layout.addLayout(hbox)

        if customBtns:
            if customBtns:
                btn_layout = QHBoxLayout()
                btn_layout.addStretch(1)
                for btn in customBtns:
                    btn : QPushButton
                    btn_layout.addWidget(btn)
                    # btn.clicked.connect(self.accept)
                layout.addLayout(btn_layout)
        else:
            btn = QPushButton("OK")
            btn.setFixedWidth(100)
            btn.clicked.connect(self.accept)

            btn_layout = QHBoxLayout()
            btn_layout.addStretch(1)
            btn_layout.addWidget(btn)

            layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(get_icon_path(POPUP_ICON)))

        def get_content_height():
            # content_height = int(text_edit.document().size().height() +100)
            content_height = int(text_edit.document().size().height() +50)
            self.resize(400, content_height if content_height < 400 else 400)

        QTimer.singleShot(0, get_content_height)

    def run_excec(self):
        if hasattr(self, "exec"):
            self.exec()
        else:
            self.exec_()

        # self.show()

    @staticmethod
    def question(parent, text):
        yes_button = QPushButton("🙆Yes")
        no_button = QPushButton("🙅Cancel")
        dialog = ShigeInfo(text, parent, type="question", customBtns=[yes_button, no_button])

        def on_yes():
            dialog.response = True
            dialog.accept()

        def on_no():
            dialog.response = False
            dialog.reject()

        yes_button.clicked.connect(on_yes)
        no_button.clicked.connect(on_no)

        dialog.run_excec()
        return dialog.response


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    info_dialog_00 = ShigeInfo(text="warning", type="warning")
    info_dialog_01 = ShigeInfo(text="critical", type="critical")
    info_dialog_02 = ShigeInfo(text="question", type="question")
    info_dialog_03 = ShigeInfo(text="lightbulb", type="lightbulb")
    info_dialog_04 = ShigeInfo(text="notice", type="notice")


    sys.exit(app.exec())