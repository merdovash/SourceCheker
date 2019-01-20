import traceback
from datetime import datetime

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox, QFileDialog, \
    QProgressBar, QApplication, QGroupBox, QFormLayout, QSpinBox

from Domain.antistud_fun import find_missing_src, NoSourcesException
from GUI.ShowResult import ResultWidget


class FileLoader(QWidget):
    run_signal = pyqtSignal('PyQt_PyObject')
    new_result = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject') # ResultWidget, str, bool

    def __init__(self, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        self.layout_ = QVBoxLayout()

        self.label = QLabel("Или просто перетащите файл(ы) в окно")
        self.layout_.addWidget(self.label, 99, alignment=Qt.AlignCenter)

        self.settings = QGroupBox('Настройки')
        self.settings_layout = QFormLayout()
        self.settings.setLayout(self.settings_layout)

        self.min_year = QSpinBox()
        self.min_year.setRange(1970, datetime.now().year)
        self.min_year.setValue(2000)
        self.settings_layout.addRow(QLabel('Минимальный год'), self.min_year)

        self.view_type_checkbox = QCheckBox()
        self.view_type_checkbox.setChecked(True)
        self.settings_layout.addRow(QLabel("Открыть в этом окне"),self.view_type_checkbox)

        self.auto_save = QCheckBox()
        self.auto_save.setChecked(False)
        self.settings_layout.addRow(QLabel('Автоматически сохранить отчет'), self.auto_save)

        self.btn = QPushButton("Выбрать файл")
        self.btn.clicked.connect(self.select_file)
        self.layout_.addWidget(self.btn, alignment=Qt.AlignCenter)

        self.layout_.addWidget(self.settings)

        self.setLayout(self.layout_)
        self.result_widgets = []

        self.setAcceptDrops(True)

        self.run_signal.connect(self.run)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            try:
                print(url.toLocalFile())
                self.run_signal.emit(url.toLocalFile())
            except Exception as exception:
                QMessageBox.critical(self, "Ошибка", str(exception))

    def select_file(self):
        file_name_dialog = QFileDialog()
        file_name_dialog.setNameFilters(['Microsoft Word (*.doc, *docx)'])

        if file_name_dialog.exec_():
            try:
                filenames = file_name_dialog.selectedFiles()
                self.run_signal.emit(filenames[0])
            except Exception as exception:
                QMessageBox.critical(self, "Ошибка", "Во время чтения прозошла ошибка: "+str(exception))

    @pyqtSlot('PyQt_PyObject', name='run')
    def run(self, filename):
        layout_ = QVBoxLayout()
        label = QLabel("Обработка файла: {}".format(filename))
        layout_.addWidget(label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        message = QLabel()
        layout_.addWidget(message, alignment=Qt.AlignCenter)

        layout_.addWidget(progress_bar)

        self.layout().addLayout(layout_)

        def progress_bar_update(text='', value=0):
            progress_bar.setValue(value)
            message.setText(text)
            QApplication.instance().processEvents()

        try:
            data, missing, old = find_missing_src(filename, progress_bar_update, **self.config())

            result_widget = ResultWidget(data, missing, old, filename)
            if self.auto_save.isChecked():
                result_widget.save(auto=True)

            self.new_result.emit(result_widget, filename, self.view_type_checkbox.isChecked())
        except NoSourcesException:
            QMessageBox.critical(self, "Ошибка", "Раздел с источниками не обнаружен")
        except Exception as exception:
            QMessageBox.critical(self, "Ошибка", "Во время чтения файла произошла ошибка" + str(exception))
            traceback.print_exc(exception)


        finally:
            self.layout().removeItem(layout_)
            progress_bar.setParent(None)
            progress_bar.deleteLater()
            label.setParent(None)
            label.deleteLater()
            message.setParent(None)
            message.deleteLater()
            layout_.deleteLater()
            QApplication.instance().processEvents()

    def config(self):
        return dict(
            min_year=self.min_year.value()
        )