from typing import List

from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem

from Domain.antistud_fun import SourceData


class TreeWidget(QTreeWidget):
    def __init__(self, sources:List[SourceData]):
        super().__init__()

        self.setColumnCount(2)
        self.setHeaderLabels(['Просмотр', 'Текст'])
        self.resizeColumnToContents(1)

        for source in sources:
            source_item = QTreeWidgetItem()
            source_item.setText(0, str(source.index))

            self_text = QTreeWidgetItem()
            self_text.setText(0, 'Источник')
            self_text.setText(1, str(source.text))
            source_item.addChild(self_text)

            links_item = QTreeWidgetItem()
            links_item.setText(0, 'Ссылки')

            if source.has_links:
                for index, link in enumerate(source.links):
                    link_item = QTreeWidgetItem()
                    link_item.setText(0, str(index+1))
                    link_item.setText(1, link)
                    links_item.addChild(link_item)

                source_item.addChild(links_item)

            self.addTopLevelItem(source_item)

        self.setUniformRowHeights(False)
        self.setWordWrap(True)



