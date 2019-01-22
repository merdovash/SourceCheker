import traceback
from datetime import datetime

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QMessageBox, QFileDialog, \
    QProgressBar, QApplication, QGroupBox, QFormLayout, QSpinBox, QInputDialog

from Domain.antistud_fun import find_missing_src, NoSourcesException
from GUI import Text
from GUI.ShowResult import ResultWidget


class FileLoader(QWidget):
    run_signal = pyqtSignal('PyQt_PyObject')
    new_result = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')  # ResultWidget, str, bool

    def __init__(self, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)
        lang = 'ru'

        self.layout_ = QVBoxLayout()

        self.label = QLabel("Или просто перетащите файл(ы) в окно")
        self.layout_.addWidget(self.label, 99, alignment=Qt.AlignCenter)

        self.settings = QGroupBox(Text.text[lang]['settings_group_label'])
        self.settings_layout = QFormLayout()
        self.settings.setLayout(self.settings_layout)

        self.min_year = QSpinBox()
        self.min_year.setRange(1900, datetime.now().year)
        self.min_year.setValue(2000)
        self.min_year.setToolTip(Text.text[lang]['min_year_tooltip'])
        min_year_label = QLabel(Text.text[lang]['min_year_label'])
        min_year_label.setToolTip(Text.text[lang]['min_year_tooltip'])
        self.settings_layout.addRow(min_year_label, self.min_year)

        self.view_type_checkbox = QCheckBox()
        self.view_type_checkbox.setChecked(True)
        self.view_type_checkbox.setToolTip(Text.text[lang]['view_type_checkbox_tooltip'])
        view_type_checkbox_label = QLabel(Text.text[lang]['view_type_checkbox_label'])
        view_type_checkbox_label.setToolTip(Text.text[lang]['view_type_checkbox_tooltip'])
        self.settings_layout.addRow(view_type_checkbox_label, self.view_type_checkbox)

        self.auto_save = QCheckBox()
        self.auto_save.setChecked(False)
        self.auto_save.setToolTip(Text.text[lang]['auto_save_tooltip'])
        auto_save_label = QLabel(Text.text[lang]['auto_save_label'])
        auto_save_label.setToolTip(Text.text[lang]['auto_save_tooltip'])
        self.settings_layout.addRow(auto_save_label, self.auto_save)

        self.check_authors = QCheckBox()
        self.check_authors.setChecked(True)
        self.check_authors.setToolTip(Text.text[lang]['check_authors_tooltip'])
        check_authors_label = QLabel(Text.text[lang]['check_authors_label'])
        check_authors_label.setToolTip(Text.text[lang]['check_authors_tooltip'])
        self.settings_layout.addRow(check_authors_label, self.check_authors)

        self.search_links = QCheckBox()
        self.search_links.setChecked(False)
        self.search_links.setToolTip("Для каждого источника будут собран спсиок параграфов, в которых имеется ссылка."
                                     "\n(Может замедлить процесс анализа)")
        search_links_label = QLabel("Собрать списки ссылок на источники")
        search_links_label.setToolTip("Для каждого источника будут собран спсиок параграфов, в которых имеется ссылка."
                                      "\n(Может замедлить процесс анализа)")
        self.settings_layout.addRow(search_links_label, self.search_links)

        self.btn = QPushButton(Text.text[lang]['select_file_btn'])
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
                self.run_signal.emit(url.toLocalFile())
            except Exception as exception:
                QMessageBox().critical(self, "Ошибка", str(exception))

    def select_file(self):
        file_name_dialog = QFileDialog()
        file_name_dialog.setNameFilters(['Microsoft Word (*.docx)'])

        if file_name_dialog.exec_():
            try:
                filenames = file_name_dialog.selectedFiles()
                for filename in filenames:
                    self.run_signal.emit(filename)
            except Exception as exception:
                QMessageBox().critical(self, "Ошибка", "Во время чтения прозошла ошибка: " + str(exception))

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
            sources = find_missing_src(filename, progress_bar_update, **self.config())

            result_widget = ResultWidget(sources, filename, **self.config())
            if self.auto_save.isChecked():
                result_widget.save(auto=True)

            self.new_result.emit(result_widget, filename, self.view_type_checkbox.isChecked())
        except NoSourcesException:
            QMessageBox().critical(self, "Ошибка", "Раздел с источниками не обнаружен")
        except Exception as exception:
            QMessageBox().critical(self, "Ошибка", "Во время чтения файла произошла ошибка" + str(exception))
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
            min_year=self.min_year.value(),
            check_authors=self.check_authors.isChecked(),
            search_links=self.search_links.isChecked(),
            declare_text=lambda: QInputDialog().getText(
                self,
                "Заголовок списка литератур не найден",
                "Укажите заголовок списка литературы."
            )
        )
