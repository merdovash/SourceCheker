from collections import Counter
from pathlib import Path
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QFileDialog, \
    QMessageBox, QLabel, QTabWidget, QTableView, QScrollBar, QAbstractItemView, QLineEdit, QFormLayout, QTreeView

from Domain import get_missing_sources, without_none
from Domain.antistud_fun import get_year, SourceData
from Domain.generate_file import generate

from PyQtPlot.StackedBar import QStackedBarWidget

from GUI.QSourceList import QSourceModel
from GUI.TreeView import TreeWidget


class ResultWidget(QWidget):
    def __init__(self, sources: List[SourceData], source_file, flags=None, *args, **kwargs):
        super().__init__(flags, *args)
        self.source_file = source_file

        self.tab = QTabWidget()

        self.missing_list = QListWidget()
        self.missing_links = [x.to_str() for x in sources if not x.has_links]
        self.missing_list.addItems(self.missing_links)
        self.tab.addTab(self.missing_list, "Список пропущенных источников")

        self.old_list = QListWidget()
        self.old_links = [source.to_str()
                          for source in sources
                          if source.is_modern is not None and not source.is_modern]
        self.old_list.addItems(self.old_links)
        self.tab.addTab(self.old_list, "Список устаревших источников")

        data = without_none([source.year for source in sources])
        self.histogram = QStackedBarWidget(flags=self)

        normal_sources_years = Counter(without_none([source.year
                                                     for source in sources
                                                     if source.is_modern and source.has_links]))
        if len(normal_sources_years):
            self.histogram.add_plot(normal_sources_years, name='Прошли проверку', color=QColor(50, 200, 50))

        old_sources_years = Counter(without_none([source.year
                                                  for source in sources
                                                  if source.is_modern is not None
                                                  and not source.is_modern
                                                  and source.has_links]))
        if len(old_sources_years):
            self.histogram.add_plot(old_sources_years, name='Устарели', color=QColor(200,200,50))

        missing_sources_years = Counter(without_none([source.year
                                                      for source in sources
                                                      if not source.has_links]))
        if len(missing_sources_years):
            self.histogram.add_plot(missing_sources_years, name='Отсутвуют ссылки', color=QColor(200,50,50))

        self.histogram.set_tooltip_func(lambda x, y, name: '{name}\nгод: {x}\nисточников: {y}'
                                        .format(x=x, y=y, name=name))
        self.histogram.horizontal_ax.set_ticks(range(min(data), max(data) + 2))
        self.tab.addTab(self.histogram, "Распределение всех источников по годам")

        self.complete_table = QTableView()
        self.complete_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.complete_table.setModel(QSourceModel(sources))
        self.complete_table.setWordWrap(True)
        self.complete_table.setTextElideMode(Qt.ElideMiddle)
        self.complete_table.setColumnWidth(0, 100)
        self.complete_table.setColumnWidth(1, 600)
        self.complete_table.resizeRowsToContents()
        self.tab.addTab(self.complete_table, 'Полная таблица')

        if kwargs.get('search_links', False):
            self.deep_table = TreeWidget(sources)
            self.tab.addTab(self.deep_table, "Просмотр ссылок")

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
                if name != '':
                    path = str(Path(name).with_suffix('.docx'))
                    save(path)
            except Exception as exception:
                QMessageBox.critical(self, "Ошибка", "Во время сохранения произошла ошибка\n" + str(exception))
        else:
            save(str(prepared_name))
