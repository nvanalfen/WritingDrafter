import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, \
                            QWidget, QVBoxLayout, QPushButton, QGraphicsView, \
                            QGraphicsScene, QGraphicsItem, QLabel, QInputDialog, \
                            QGraphicsRectItem, QGraphicsTextItem)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush, QFontMetrics

class EditableTextItem(QGraphicsTextItem):
    def __init__(self, text, parent=None):
        super(EditableTextItem, self).__init__(text, parent)

    def focusOutEvent(self, event):
        # When focus is lost, disable text editing
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        super(EditableTextItem, self).focusOutEvent(event)

class DraggableTextItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        super(DraggableTextItem, self).__init__(parent)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)

        # Create a text item as a child of the rectangle
        self.textItem = EditableTextItem("Edit me", self)
        self.textItem.setTextInteractionFlags(Qt.NoTextInteraction)
        self.textItem.setPos(0, 0)
        self.textItem.setTextWidth(self.rect().width())  # Set initial text width for wrapping

        # Adjust the size of the rectangle to fit the text item
        self.adjustRectSize()
    
    def paint(self, painter, option, widget=None):
        super(DraggableTextItem, self).paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        else:
            painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.drawRect(self.rect())
        
        resizeHandleRect = self.resizeHandle()
        painter.fillRect(resizeHandleRect, Qt.black)
        
        #painter.setPen(QPen(Qt.black))
        #metrics = QFontMetrics(painter.font())
        #elidedText = metrics.elidedText(self.text, Qt.ElideRight, int(self.rect().width()) - 10)
        #painter.drawText(self.rect().adjusted(5, 5, -5, -5), Qt.AlignLeft | Qt.AlignTop, elidedText)
        
    def updateSceneRect(self):
        itemRect = self.mapToScene(self.boundingRect()).boundingRect()
        scene = self.scene()
        if scene:
            currentSceneRect = scene.sceneRect()
            newSceneRect = currentSceneRect.united(itemRect)  # Unite the current scene rect with the item's rect
            
            # Optionally, add some margin
            #newSceneRect.adjust(-10, -10, 10, 10)

            if newSceneRect != currentSceneRect:
                scene.setSceneRect(newSceneRect)

    def adjustRectSize(self):
        # Set the rectangle size to fit the text, with some padding
        padding = 10
        rect = self.textItem.boundingRect().adjusted(-padding / 2, -padding / 2, padding / 2, padding / 2)
        self.setRect(rect)

    def mousePressEvent(self, event):
        if self.resizeHandle().contains(event.pos()):
            self.dragStartPos = event.pos()
            self.dragStartRect = self.rect()
            self.isResizing = True
            event.accept()
        elif event.button() == Qt.LeftButton:
            self.isResizing = False
            if not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
                self.scene().clearSelection()
            self.setSelected(not self.isSelected())
            super(DraggableTextItem, self).mousePressEvent(event)
        else:
            self.isResizing = False
            super(DraggableTextItem, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isResizing:
            diff = event.pos() - self.dragStartPos
            newRect = self.dragStartRect.adjusted(0, 0, diff.x(), diff.y())
            self.setRect(newRect.normalized())
            self.textItem.setTextWidth(self.rect().width())
        else:
            super(DraggableTextItem, self).mouseMoveEvent(event)
            
        self.updateSceneRect()

    def mouseReleaseEvent(self, event):
        self.isResizing = False
        if not (event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)):
            super(DraggableTextItem, self).mouseReleaseEvent(event)
        
        self.updateSceneRect()

    def mouseDoubleClickEvent(self, event):
        # Check if the double-click is within the text item bounds to avoid conflict with resizing.
        if self.textItem.boundingRect().contains(event.pos()):
            self.textItem.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.textItem.setFocus(Qt.MouseFocusReason)
            # Ensure the text item captures the double-click event for editing.
            self.textItem.mouseDoubleClickEvent(event)
        else:
            # For clicks outside the text item (e.g., on the resize handle), maintain default behavior.
            super(DraggableTextItem, self).mouseDoubleClickEvent(event)
            self.adjustRectSize()

    def resizeHandle(self):
        size = 10
        return QRectF(self.rect().right() - size, self.rect().bottom() - size, size, size)

class CanvasTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFixedSize(640, 480)
        self.scene.setSceneRect(0, 0, 640, 480)

        self.addButton = QPushButton("Add Text Box")
        self.addButton.clicked.connect(self.addTextBox)
        self.deleteButton = QPushButton("Delete Selected Text Box")
        self.deleteButton.clicked.connect(self.deleteSelectedTextBox)

        layout.addWidget(self.addButton)
        layout.addWidget(self.view)
        layout.addWidget(self.deleteButton)

    def addTextBox(self):
        item = DraggableTextItem()
        self.scene.addItem(item)

    def deleteSelectedTextBox(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 App with Draggable and Resizable Text Boxes")

        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        self.welcomeTab = QLabel("Welcome to the PyQt5 App!")
        self.canvasTab = CanvasTab()

        self.tabWidget.addTab(self.welcomeTab, "Welcome")
        self.tabWidget.addTab(self.canvasTab, "Canvas")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
