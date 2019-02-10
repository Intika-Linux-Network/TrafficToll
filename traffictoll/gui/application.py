import sys

from PyQt5.QtWidgets import QApplication

from traffictoll.gui.mainwindow import MainWindow


def start():
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    application.exec()
