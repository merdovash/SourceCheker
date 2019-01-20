from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QFileDialog, \
    QMessageBox, QLabel, QTabWidget, QTableView, QScrollBar, QAbstractItemView, QLineEdit, QFormLayout

from Domain import get_missing_sources
from Domain.antistud_fun import get_year
from Domain.generate_file import generate

from PyQtPlot.HistogramWidget import Histogram

from GUI.QSourceList import QSourceModel


class ResultWidget(QWidget):
    def __init__(self, sources, missing, old, source_file, flags=None, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)
        self.source_file = source_file

        self.tab = QTabWidget()

        self.missing_list = QListWidget()
        self.missing_links = get_missing_sources(sources, missing)
        self.missing_list.addItems(self.missing_links)
        self.tab.addTab(self.missing_list, "Список пропущенных источников")

        self.old_list = QListWidget()
        self.old_links = ["{i}. {text}".format(i=i, text=text) for i, text in enumerate(sources) if i in old]
        self.old_list.addItems(self.old_links)
        self.tab.addTab(self.old_list, "Список устаревших источников")

        data = [x for x in [get_year(source) for source in sources] if x is not None]
        self.histogram = Histogram(data, source_file, self)
        self.histogram.set_tooltip_func(lambda x, y, name: 'год: {x}\nисточников: {y}'.format(x=x, y=y))
        self.histogram.horizontal_ax.set_ticks(range(min(data), max(data)))
        self.tab.addTab(self.histogram, "Распределение всех источников по годам")

        self.table = QTableView()
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setModel(QSourceModel(sources, missing))
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideMiddle)
        self.table.setColumnWidth(0, 600)
        self.table.resizeRowsToContents()
        self.tab.addTab(self.table, 'Полная таблица')

        self.setWindowTitle("Результат проверки {source_file}".format(source_file=source_file))

        self.layout_ = QVBoxLayout()

        self.head_layout = QHBoxLayout()

        self.copy_button = QPushButton("Скопировать список пропущенных\nисточников в буффер")
        self.copy_button.clicked.connect(self.copy)

        self.save_btn_layout = QVBoxLayout()

        self.save_button = QPushButton("Cформировать отчет в формате docx")
        self.save_button.clicked.connect(self.save)
        self.save_btn_layout.addWidget(self.save_button)

        self.saved_file_info = QWidget()
        self.saved_file_info.setVisible(False)

        saved_path_layout = QFormLayout()

        self.save_path = QLineEdit()
        self.save_path.setReadOnly(True)

        saved_path_layout.addRow(QLabel('Файл сохранен'), self.save_path)

        self.saved_file_info.setLayout(saved_path_layout)
        self.save_btn_layout.addWidget(self.saved_file_info)

        self.head_layout.addWidget(self.copy_button, stretch=2)
        self.head_layout.addLayout(self.save_btn_layout, stretch=6)

        self.file_label = QLabel(source_file)
        self.total_label = QLabel('Всего пропущено ссылок {} из {}'.format(len(self.missing_links), len(sources)))

        self.layout_.addWidget(self.file_label)
        self.layout_.addWidget(self.total_label)

        self.layout_.addLayout(self.head_layout)

        self.layout_.addWidget(self.tab)

        self.setLayout(self.layout_)

    def copy(self):
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText('\n'.join(self.missing_links))
        except Exception as exception:
            QMessageBox.critical(self,
                                 "Ошибка",
                                 "Во время копирования в буфер обмена произошла ошибка: " + str(exception))

    def save(self, auto=False):
        def save(target_file):
            generate(self.missing_links, self.old_links, target_file)
            QMessageBox.information(self, "Файл сохранен", "Файл сохранен: {name}".format(name=target_file))

            self.saved_file_info.setVisible(True)
            self.save_path.setText(target_file)
        prepared_name = Path(self.source_file)
        prepared_name = prepared_name.with_name('[Проверка источников] ' + prepared_name.name).with_suffix('.docx')
        if not auto:
            try:
                name, ext = QFileDialog().getSaveFileName(
                    self,
                    "Сохранить отчет",
                    str(prepared_name),
                    'Microsoft Word (*.docx)',
                    'Microsoft Word (*.docx)'
                )
                if name!='':
                    path = str(Path(name).with_suffix('.docx'))
                    save(path)
            except Exception as exception:
                QMessageBox.critical(self, "Ошибка", "Во время сохранения произошла ошибка\n" + str(exception))
        else:
            save(str(prepared_name))

