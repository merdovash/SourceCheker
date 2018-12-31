from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from GUI.FileLoader import FileLoader


class MainWidget(QWidget):
    def __init__(self, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        self.layout_ = QVBoxLayout()
        self.tab = QTabWidget()

        self.file_loader = FileLoader(self)
        self.file_loader.new_result.connect(self.show_result)

        self.tab.addTab(self.file_loader, "Выбор файла")
        self.tab.setTabsClosable(True)
        self.tab.tabCloseRequested.connect(self.tab_close_request)

        self.layout_.addWidget(self.tab)

        self.setLayout(self.layout_)

        self.results = []

    def show_result(self, result, name, in_tabs):
        if in_tabs:
            self.tab.addTab(result, name.split('/')[-1])
            if self.tab.currentIndex() == 0:
                self.tab.setCurrentWidget(result)
        else:
            self.results.append(result)
            result.show()

    def tab_close_request(self, closing_tab_index):
        if closing_tab_index == 0:
            return
        self.tab.removeTab(closing_tab_index)
