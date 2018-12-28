from PyQt5.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QApplication, \
    QHBoxLayout, QProgressBar

from Domain.antistud_fun import findMissingSrc
from GUI.ShowResult import ResultWidget


class FileSelectorWidget(QWidget):
    run_signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        self.layout_ = QVBoxLayout()

        self.label = QLabel("Или просто перетащите файл(ы) в окно")
        self.layout_.addWidget(self.label, 99)

        self.btn = QPushButton("Выбрать файл")
        self.btn.clicked.connect(self.select_file)
        self.layout_.addWidget(self.btn)

        self.setLayout(self.layout_)
        self.result_widgets = []

        self.setAcceptDrops(True)

        self.run_signal.connect(self.run)

    def dragEnterEvent(self, e):
        # print(e)
        print(e.mimeData().hasUrls())
        # print(e.mimeData().urls())
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            try:
                print(url.toLocalFile())
                self.run_signal.emit(url.toLocalFile())
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def select_file(self):
        file_name_dialog = QFileDialog()
        file_name_dialog.setNameFilters(['Microsoft Word (*.doc, *docx)'])

        if file_name_dialog.exec_():
            try:
                filenames = file_name_dialog.selectedFiles()
                self.run_signal.emit(filenames[0])
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", "Во время чтения прозошла ошибка")

    @pyqtSlot('PyQt_PyObject', name='run')
    def run(self, filename):
        l = QVBoxLayout()
        label = QLabel("Обработка файла: {}".format(filename))
        l.addWidget(label)

        bar = QProgressBar()
        bar.setRange(0,100)
        message = QLabel()
        l.addWidget(message, alignment=Qt.AlignCenter)

        l.addWidget(bar)

        self.layout().addLayout(l)

        def progress_bar(text='', value=0):
            QApplication.instance().processEvents()
            bar.setValue(value)
            message.setText(text)
        try:
            data, missing = findMissingSrc(filename, progress_bar)

            data_ = []
            for index, item in enumerate(data):
                if index in missing:
                    data_.append('{}. {}'.format(index + 1, item))

            result_widget = ResultWidget(data_, filename, len(data))
            self.layout().removeItem(l)
            bar.deleteLater()
            label.deleteLater()
            message.deleteLater()
            l.deleteLater()
            QApplication.instance().processEvents()
            result_widget.show()
            self.result_widgets.append(result_widget)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Во время чтения файла произошла ошибка"+str(e))
