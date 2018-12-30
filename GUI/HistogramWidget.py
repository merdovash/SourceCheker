import re
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from GUI.Bar import Histogram


class HistogramWidget(QWidget):
    def __init__(self, sources, flags, *args, **kwargs):
        super().__init__(flags, *args, **kwargs)

        current_year = datetime.now().year

        years = []
        for text in sources:
            year = re.findall('[1-2][0-9]{3}', text)
            year = map(lambda x: int(x), year)
            year = list(filter(lambda x: x <= current_year, year))

            have_any_years = len(year) > 0
            if have_any_years:
                years.append(max(year))

        layout = QVBoxLayout()

        have_some_data_to_plot = len(years) > 0
        print(years)
        if have_some_data_to_plot:
            self.hist = Histogram(years, self)
            self.hist.set_x_ticks(list(range(min(1990, min(years)), current_year+1)))
            self.hist.set_x_ticks_rotate(60)
            self.hist.set_x_ticks_offset(20)
            layout.addWidget(self.hist)

        else:
            layout.addWidget(QLabel('Нечего показывать'), alignment=Qt.AlignCenter)

        self.setLayout(layout)
