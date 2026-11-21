"""Application startup."""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from .resources import APP_ICON_PATH
from .window import HexVaWindow


def main() -> None:
    app = QApplication([])
    app.setApplicationName("HexVa")
    app.setOrganizationName("Juromito")
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    window = HexVaWindow()
    window.show()
    app.exec()
