from typing import List

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from PyQt5.QtGui import QColor

from Domain.antistud_fun import get_year, SourceData


class QSourceModel(QAbstractTableModel):
    year_col = 0
    text_col = 1

    def __init__(self, sources):
        super().__init__()
        self.sources: List[SourceData] = sources

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.sources)

    def columnCount(self, parent=None, *args, **kwargs):
        return 2

    def data(self, index: QModelIndex, role=None):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == self.year_col:
                return self.sources[row].year
            if col == self.text_col:
                return self.sources[row].text

        if role == Qt.BackgroundColorRole:
            if col == self.year_col:
                if not self.sources[row].has_links:
                    return QColor(200, 50, 50, 100)
                if not self.sources[row].is_modern:
                    return QColor(200, 200, 50, 100)
            if col == self.text_col:
                if not self.sources[row].has_links:
                    return QColor(255, 0, 0, 100)
                if not self.sources[row].is_modern:
                    return QColor(200, 200, 100, 140)

        if role == Qt.TextAlignmentRole:
            if col == self.year_col:
                return Qt.AlignHCenter

        if role == Qt.ToolTipRole:
            if col == self.text_col:
                if not self.sources[row].has_links:
                    return "На данный источник отсутсвует ссылка"
                if not self.sources[row].is_modern:
                    return "Источник устарел"

        return QVariant()

    def headerData(self, p_int, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return ['Год', 'Информация об источнике'][p_int]
        return QVariant()
