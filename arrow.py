from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QPen, QPainterPath, QPainter, QColor
import math

class ArrowItem(QGraphicsLineItem):
    def __init__(self, startItem, endItem, parent=None):
        super(ArrowItem, self).__init__(parent)
        self.startItem = startItem
        self.endItem = endItem
        self.setPen(QPen(Qt.black, 2))
        self.updatePosition()

    def updatePosition(self):
        startCenter = self.startItem.sceneBoundingRect().center()
        endCenter = self.endItem.sceneBoundingRect().center()
        self.setLine(QLineF(startCenter, endCenter))

    def paint(self, painter, option, widget=None):
        if self.startItem and self.endItem:
            self.updatePosition()
            super(ArrowItem, self).paint(painter, option, widget)

            # Arrow head drawing simplified
            line = self.line()
            arrowSize = 10.0
            angle = math.radians(line.angle())

            p1 = line.p1()
            p2 = line.p2()
            dx = arrowSize * math.sin(angle)
            dy = arrowSize * math.cos(angle)

            arrowP1 = p2 - QPointF(dx, dy)
            arrowP2 = p2 + QPointF(dy, -dx)

            arrowHead = QPainterPath()
            arrowHead.moveTo(p2)
            arrowHead.lineTo(arrowP1)
            arrowHead.lineTo(arrowP2)
            arrowHead.lineTo(p2)

            painter.setBrush(QColor(Qt.black))
            painter.drawPath(arrowHead)
