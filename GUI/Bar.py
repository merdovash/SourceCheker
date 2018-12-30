import sys
from collections import Counter
from math import cos, sin
from operator import xor
from random import randint

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3


class Bar(QWidget):
    def __init__(self, bars, heights, flags, x_tick_rotation=0, *args, **kwargs):
        assert len(bars) == len(heights)
        super().__init__(flags, *args, **kwargs)

        self.bars = bars
        self._x_ticks = bars
        self.heights = heights

        self._map = {bars[i]: heights[i] for i in range(len(bars))}

        self.margin = (0.1, 0.1, 0.1, 0.1)

        self.color = QColor(255, 128, 0)
        self.bg_color = QColor(255, 255, 255)

        self.y_tick_width = 6
        self.x_tick_width = 6

        self.x_tick_rotation = x_tick_rotation
        self._x_ticks_margin = 0

        self.item_color = QColor(255, 128, 0)

        self.item_width = 0.75

        self.font = QFont()
        self.font.setPixelSize(20)

    def paintEvent(self, QPaintEvent):
        painter = QPainter()
        painter.begin(self)

        painter.setFont(self.font)

        width = self.width()
        height = self.height()

        painter.fillRect(0, 0, width, height, self.bg_color)

        top, right, bottom, left = self._cal_margin()

        painter.drawLine(left, top, left, height - bottom)
        painter.drawLine(left, height - bottom, width - right, height - bottom)

        y_tick_count = max(self.heights) + 1
        y_ax_size = height - bottom - bottom
        y_tick_interval = y_ax_size / y_tick_count
        for i in range(y_tick_count):
            y_pos = (height - bottom) - i * y_tick_interval
            painter.drawLine(left - self.y_tick_width / 2, y_pos, left + self.y_tick_width / 2, y_pos)

            painter.drawText(
                QRect(0, y_pos - y_tick_interval / 2, left - self.y_tick_width / 2 - 4, y_tick_interval),
                xor(Qt.AlignVCenter, Qt.AlignRight),
                str(i))

        x_tick_count = len(self._x_ticks)
        x_ax_size = width - left - right
        x_tick_interval = x_ax_size / x_tick_count
        x_ax_y_pos = height - bottom
        for i in range(x_tick_count):
            x_pos = left + (i + 0.5) * x_tick_interval
            painter.drawLine(x_pos, x_ax_y_pos - self.x_tick_width / 2, x_pos, x_ax_y_pos + self.x_tick_width / 2)

            if self.x_tick_rotation != 0:
                painter.translate(x_pos, x_ax_y_pos + self.x_tick_width / 2 + 4)
                painter.rotate(-self.x_tick_rotation)
                painter.translate(-x_pos, -(x_ax_y_pos + self.x_tick_width / 2 + 4))
                painter.drawText(
                    QRect(
                        x_pos - x_tick_interval / 2+self._x_ticks_margin*cos(self.x_tick_rotation),
                        x_ax_y_pos + (self.x_tick_width / 2 + 4)*cos(self.x_tick_rotation)-self._x_ticks_margin*sin(
                            self.x_tick_rotation),
                        50,
                        bottom),
                    Qt.AlignHCenter,
                    str(self._x_ticks[i])
                )
                painter.resetTransform()
            else:
                painter.drawText(
                    QRect(
                        x_pos - x_tick_interval / 2,
                        x_ax_y_pos + self.x_tick_width / 2 + 4+self._x_ticks_margin,
                        x_tick_interval,
                        bottom),
                    Qt.AlignHCenter,
                    str(self._x_ticks[i])
                )

        for bar, h in self._map.items():
            x_pos = left + self._x_ticks.index(bar) * x_tick_interval
            painter.fillRect(
                QRect(
                    x_pos + (1 - self.item_width) * x_tick_interval / 2,
                    x_ax_y_pos,
                    x_tick_interval * self.item_width,
                    -h * y_tick_interval),
                self.item_color
            )

        painter.end()

    def _cal_margin(self):
        return self.height() * self.margin[TOP], self.width() * self.margin[RIGHT], self.height() * self.margin[BOTTOM], \
               self.width() * self.margin[LEFT]

    def set_x_ticks(self, ticks):
        self._x_ticks = ticks

    def set_x_ticks_offset(self, val):
        self._x_ticks_margin = val

    def set_x_ticks_rotate(self, val):
        self.x_tick_rotation = val


class Histogram(Bar):
    def __init__(self, data, flags, *args, **kwargs):
        counter = Counter(data)
        bars = list(range(min(counter.keys()), max(counter.keys())))
        heights = []
        for i in bars:
            if i in counter.keys():
                heights.append(counter[i])
            else:
                heights.append(0)

        super().__init__(bars, heights, flags, *args, **kwargs)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QMainWindow()
    hist = Histogram([randint(1995, 2014) for _ in range(randint(20, 50))], window,
                     x_tick_rotation=60)

    hist.set_x_ticks(list(range(1990, 2018)))
    hist.set_x_ticks_offset(20)
    window.setCentralWidget(hist)

    window.show()

    sys.exit(app.exec_())
