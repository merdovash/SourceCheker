from PyQt5.QtCore import QModelIndex, Qt, QVariant, QAbstractTableModel
from PyQt5.QtGui import QColor

from Domain.antistud_fun import get_year


class QSourceModel(QAbstractTableModel):
    year_col = 0
    text_col = 1

    def __init__(self, sources, missing):
        super().__init__()
        self.sources = sources
        self.missing = missing

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.sources)

    def columnCount(self, parent=None, *args, **kwargs):
        return 2

    def data(self, index: QModelIndex, role=None):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            if col == self.year_col:
                return self.sources[row]
            if col == self.text_col:
                return get_year(self.sources[row])

        if role == Qt.BackgroundColorRole:
            if col == self.text_col:
                years = [x for x in [get_year(x) for x in self.sources] if x is not None]
                year = get_year(self.sources[row])
                if year is not None:
                    min_year = min(years)
                    max_year = max(years)
                    k = ((year - min_year) / (max_year - min_year))
                    return QColor(255 - int(255 * k), int(255 * k), 0, 100)
                return QColor(100, 100, 100, 100)
            if col == self.year_col:
                if row in self.missing:
                    return QColor(255, 0, 0, 100)

        if role == Qt.TextAlignmentRole:
            if col == self.text_col:
                return Qt.AlignHCenter

        if role == Qt.ToolTipRole:
            if col == self.year_col:
                if row in self.missing:
                    return "На данный источник отсутсвует ссылка"

        return QVariant()

    def headerData(self, p_int, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return ['Описание источника', 'Год'][p_int]
        return QVariant()
