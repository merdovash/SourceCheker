from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QFileDialog, \
    QMessageBox, QLabel

from Domain.generate_file import generate


class ResultWidget(QWidget):
    def __init__(self, missing_links, source_file, total_sources, flags=None, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)
        self.source_file = source_file

        self.list = QListWidget()
        self.list.addItems(missing_links)
        self.missing_links = missing_links

        self.setWindowTitle("Результат проверки {source_file}".format(source_file=source_file))

        self.layout_ = QVBoxLayout()

        self.head_layout = QHBoxLayout()
        self.copy_button = QPushButton("Скопировать всё в буффер")
        self.save_button = QPushButton("Скачать в формате docx")

        self.copy_button.clicked.connect(self.copy)
        self.save_button.clicked.connect(self.save)

        self.head_layout.addWidget(self.copy_button)
        self.head_layout.addWidget(self.save_button)

        self.file_label = QLabel(source_file)
        self.total_label = QLabel('Всего пропущено ссылок {} из {}'.format(len(missing_links), total_sources))

        self.layout_.addWidget(self.file_label)
        self.layout_.addWidget(self.total_label)

        self.layout_.addLayout(self.head_layout)

        self.layout_.addWidget(self.list)

        self.setLayout(self.layout_)

    def copy(self):
        try:
            cb = QApplication.clipboard()
            cb.setText('\n'.join(self.missing_links))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", "Во время копирования в буфер обмена произошла ошибка: "+str(e))

    def save(self):
        try:
            file_name_target = QFileDialog()
            file_name_target.setNameFilters(['Microsoft Word (*.docx)'])
            file_name_target.selectNameFilter('Microsoft Word (*.docx)')
            file_name_target.setDefaultSuffix('docx')
            if file_name_target.exec_():
                name = file_name_target.selectedFiles()[0]
                generate(self.missing_links, name)
                QMessageBox.information(self, "Файл сохранен", "Файл сохранен: {name}".format(name=name))
        except Exception as e:
            QMessageBox.critical(self,"Ошибка", "Во время сохранения произошла ошибка\n"+str(e))



