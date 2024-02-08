from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QPen, QPolygonF, QPainterPath, QPainter, QColor
import math

class ArrowItem(QGraphicsLineItem):
    def __init__(self, startItem, endItem, parent=None):
        super(ArrowItem, self).__init__(parent)
        self.setZValue(-10)
        self.startItem = startItem
        self.endItem = endItem
        self.setFlag(QGraphicsItem.ItemIsSelectable)  # Allow selection
        self.setPen(QPen(Qt.black, 2))
        self.updatePosition()

    def lineRectIntersection(self, center1, center2, rect):
        """
        Calculate the intersection point of a line (defined by two centers) with a rectangle.
        Only works for axis-aligned rectangles and lines.
        """
        dx = center2.x() - center1.x()
        dy = center2.y() - center1.y()
        
        # For vertical lines, handle separately to avoid division by zero
        if dx == 0:
            if center2.y() > rect.top() and center2.y() < rect.bottom():
                return QPointF(center1.x(), rect.top() if center1.y() > center2.y() else rect.bottom())
            return center1
        
        # Calculate intersection with vertical sides
        slope = dy / dx
        intercept = center1.y() - slope * center1.x()
        
        # Intersection with left side
        y_left = slope * rect.left() + intercept
        if y_left >= rect.top() and y_left <= rect.bottom():
            return QPointF(rect.left(), y_left)
        
        # Intersection with right side
        y_right = slope * rect.right() + intercept
        if y_right >= rect.top() and y_right <= rect.bottom():
            return QPointF(rect.right(), y_right)
        
        # Calculate intersection with horizontal sides if no vertical intersection
        x_top = (rect.top() - intercept) / slope
        if x_top >= rect.left() and x_top <= rect.right():
            return QPointF(x_top, rect.top())
        
        x_bottom = (rect.bottom() - intercept) / slope
        if x_bottom >= rect.left() and x_bottom <= rect.right():
            return QPointF(x_bottom, rect.bottom())
        
        return center1  # Fallback if no intersection found

    def nearestPoints(self, rect1, rect2):
        """
        Calculate the nearest points on the edges of two rectangles.
        """
        points = []
        
        # Center points
        center1 = rect1.center()
        center2 = rect2.center()
        
        # Determine the relative position of rect2 to rect1
        if center2.x() < rect1.left():
            x1 = rect1.left()
        elif center2.x() > rect1.right():
            x1 = rect1.right()
        else:
            x1 = center2.x()
        
        if center2.y() < rect1.top():
            y1 = rect1.top()
        elif center2.y() > rect1.bottom():
            y1 = rect1.bottom()
        else:
            y1 = center2.y()
        
        points.append(QPointF(x1, y1))
        
        # Repeat the calculation for the second rectangle, with positions relative to the first
        if center1.x() < rect2.left():
            x2 = rect2.left()
        elif center1.x() > rect2.right():
            x2 = rect2.right()
        else:
            x2 = center1.x()
        
        if center1.y() < rect2.top():
            y2 = rect2.top()
        elif center1.y() > rect2.bottom():
            y2 = rect2.bottom()
        else:
            y2 = center1.y()
        
        points.append(QPointF(x2, y2))
        
        return points

    def updatePosition(self):
        # Before updating, check if items are still in the scene
        if self.startItem.scene() is None or self.endItem.scene() is None:
            # If either item has been removed from the scene, remove the arrow too
            if self.scene():
                self.scene().removeItem(self)
            return  # Exit the method to avoid further processing
        
        startCenter = self.startItem.sceneBoundingRect().center()
        endCenter = self.endItem.sceneBoundingRect().center()
        line = QLineF(startCenter, endCenter)
        
        # Adjust the end of the line to be just before the endItem
        angle = math.radians(line.angle())
        
        # Calculate the offset to move the end point outside the endItem rectangle
        # You might need to adjust the offset based on your arrow size
        offset = 10  # Distance in pixels you want the arrow to stop before the endItem
        dx = math.cos(angle) * offset
        dy = math.sin(angle) * offset
        
        # Adjust line end point
        line.setP2(QPointF(endCenter.x() - dx, endCenter.y() - dy))
        
        self.setLine(line)

    def paint(self, painter, option, widget=None):
        if not self.startItem or not self.endItem:
            return

        self.updatePosition()

        # Calculate intersection points with the rectangles
        intersection1 = self.lineRectIntersection(self.line().p1(), self.line().p2(), self.startItem.sceneBoundingRect())
        intersection2 = self.lineRectIntersection(self.line().p1(), self.line().p2(), self.endItem.sceneBoundingRect())

        dy = intersection2.y() - intersection1.y()
        dx = intersection2.x() - intersection1.x()
        frac = 3/4
        x = intersection1.x()
        y = intersection1.y() + frac*dy
        if dx != 0:
            slope = dy / dx
            intercept = intersection1.y() - slope * intersection1.x()
            x = frac*dx + intersection1.x()
            y = slope*x + intercept
        
        # Calculate the midpoint between the intersection points
        # midPoint = QPointF((intersection1.x() + intersection2.x()) / 2,
        #                           (intersection1.y() + intersection2.y()) / 2)
        midPoint = QPointF(x,y)

        super(ArrowItem, self).paint(painter, option, widget)

        # # Calculate the midpoint of the line
        # midPoint = QPointF((self.line().p1().x() + self.line().p2().x()) / 2,
        #                    (self.line().p1().y() + self.line().p2().y()) / 2)

        # Calculate the direction of the line for the arrowhead
        angle = math.atan2(-self.line().dy(), self.line().dx())
        arrowSize = 10

        # # Create the arrowhead polygon
        arrowHead = QPolygonF()
        arrowHead.append(midPoint)
        arrowHead.append(midPoint - QPointF(math.sin(angle + math.pi / 3) * arrowSize,
                                            math.cos(angle + math.pi / 3) * arrowSize))
        arrowHead.append(midPoint - QPointF(math.sin(angle + math.pi - math.pi / 3) * arrowSize,
                                            math.cos(angle + math.pi - math.pi / 3) * arrowSize))

        painter.setBrush(Qt.black)
        painter.drawPolygon(arrowHead)

        # # Draw the arrowhead at the adjusted end of the line
        # arrowSize = 10.0
        # angle = math.atan2(-self.line().dy(), self.line().dx())
        
        # # Arrowhead points
        # intersection = self.lineRectIntersection(self.line().p1(), self.line().p2(), self.endItem.sceneBoundingRect())
        # p1 = self.line().p2() + QPointF(math.sin(angle + math.pi / 3) * arrowSize,
        #                                 math.cos(angle + math.pi / 3) * arrowSize)
        # p2 = self.line().p2() + QPointF(math.sin(angle + math.pi - math.pi / 3) * arrowSize,
        #                                 math.cos(angle + math.pi - math.pi / 3) * arrowSize)
        
        #arrowHead = QPolygonF([self.line().p2(), p1, p2])
        painter.drawPolygon(arrowHead)
        self.scene().update(self.scene().sceneRect())
