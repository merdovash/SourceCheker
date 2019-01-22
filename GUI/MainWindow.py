from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow

from GUI.MainWidget import MainWidget


class MainWindow(QMainWindow):
    def __init__(self, flags=None, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        self.setMinimumSize(QSize(500, 400))

        self.setWindowTitle("Проверка работ")

        self.setCentralWidget(MainWidget(self))
