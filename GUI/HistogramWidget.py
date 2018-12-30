import re
from collections import Counter
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class HistogramWidget(QWidget):
    def __init__(self, sources, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        layout = QVBoxLayout()

        current_year = datetime.now().year

        years = []
        for text in sources:
            year = re.findall('[1-2][0-9]{3}', text)
            year = map(lambda x: int(x), year)
            year = list(filter(lambda x: x <= current_year, year))

            have_any_years = len(years) > 0
            if have_any_years:
                years.append(max(year))

        have_some_data_to_plot = len(years) > 0
        if have_some_data_to_plot:
            self.figure = pyplot.figure()
            static_canvas = FigureCanvas(self.figure)
            layout.addWidget(static_canvas)
            layout.addWidget(NavigationToolbar(static_canvas, self))

            self._static_ax = self.figure.add_subplot(111)

            # задаем список ячеек
            bins = list(range(min(years), current_year + 2))
            # рисуем гистограму
            self._static_ax.hist(years, bins=bins, color='orange', rwidth=0.75, align='left')
            # задаем обозначения на оски х
            self._static_ax.set_xticks(list(range(min(years), current_year + 1)))
            # поворачиваем надписи на оси x
            self._static_ax.tick_params(axis="x", labelrotation=60)
            # чтобы года было видно
            self.figure.subplots_adjust(bottom=0.145)
            # задаем обозначения на оси y
            self._static_ax.set_yticks(list(range(0, max(Counter(years).values()) + 1)))

            self.setLayout(layout)
        else:
            self.setLayout(QVBoxLayout())
            self.layout().addWidget(QLabel('Нечего показывать'), alignment=Qt.AlignCenter)
