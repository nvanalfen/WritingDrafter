import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, \
                            QWidget, QVBoxLayout, QPushButton, QGraphicsView, \
                            QGraphicsScene, QGraphicsItem, QLabel, QInputDialog, \
                            QGraphicsRectItem, QGraphicsTextItem, QHBoxLayout, \
                                QSizePolicy)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QColor, QBrush, QFontMetrics

class EditableTextItem(QGraphicsTextItem):
    def __init__(self, text, parent=None):
        super(EditableTextItem, self).__init__(text, parent)
        self.parent = parent

    def focusOutEvent(self, event):
        # When focus is lost, disable text editing
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.parent.adjustRectSize()
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
        self.textItem.setZValue(1)  # Set the text in front of the background

        # Adjust the size of the rectangle to fit the text item
        self.adjustRectSize()
    
    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(QColor(255, 255, 255)))  # Solid white background
        painter.drawRect(self.rect())
        super(DraggableTextItem, self).paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(self.rect())  # Highlight the selection with a red outline
        else:
            painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.drawRect(self.rect())
        
        resizeHandleRect = self.resizeHandle()
        painter.fillRect(resizeHandleRect, Qt.black)
        
    def updateSceneRect(self):
        itemRect = self.mapToScene(self.boundingRect()).boundingRect()
        scene = self.scene()
        if scene:
            currentSceneRect = scene.sceneRect()
            newSceneRect = currentSceneRect.united(itemRect)  # Unite the current scene rect with the item's rect

            if newSceneRect != currentSceneRect:
                scene.setSceneRect(newSceneRect)

    def adjustRectSize(self):
        # Set the rectangle size to fit the text, with some padding
        padding = 10
        width = max( self.textItem.boundingRect().width()+(padding/2), self.rect().width() )
        height = max( self.textItem.boundingRect().height()+(padding/2), self.rect().height() )
        rect = QRectF(0, 0, width, height)
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
            #self.backgroundRect.setRect(newRect.normalized())  # Update background size during resize
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
        self.layout = QVBoxLayout(self)
        addDeleteLayout = QHBoxLayout()
        saveLoadLayout = QHBoxLayout()
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        #self.view.setFixedSize(640, 480)
        self.scene.setSceneRect(0, 0, 640, 480)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow view to expand

        self.addButton = QPushButton("Add Text Box")
        self.addButton.clicked.connect(self.addTextBox)
        self.deleteButton = QPushButton("Delete Selected Text Box")
        self.deleteButton.clicked.connect(self.deleteSelectedTextBox)
        self.saveButton = QPushButton("Save Canvas")
        self.saveButton.clicked.connect(lambda: self.save_canvas(self.scene, 'canvas.json'))
        self.loadButton = QPushButton("Load Canvas")
        self.loadButton.clicked.connect(lambda: self.load_canvas(self.scene, 'canvas.json'))

        addDeleteLayout.addWidget(self.addButton)
        addDeleteLayout.addWidget(self.deleteButton)
        saveLoadLayout.addWidget(self.saveButton)
        saveLoadLayout.addWidget(self.loadButton)
        self.layout.addLayout(addDeleteLayout)
        self.layout.addLayout(saveLoadLayout)
        self.layout.addWidget(self.view, 1)

        self.setLayout(self.layout)

    def addTextBox(self):
        item = DraggableTextItem()
        self.scene.addItem(item)

    def deleteSelectedTextBox(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)

    def save_canvas(self, scene, filename):
        items_data = []
        for item in scene.items():
            if isinstance(item, DraggableTextItem):  # Assuming DraggableTextItem is your custom class
                item_data = {
                    'type': 'DraggableTextItem',
                    'text': item.textItem.toPlainText(),
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'width': item.rect().width(),
                    'height': item.rect().height()
                }
                items_data.append(item_data)
        
        with open(filename, 'w') as outfile:
            json.dump(items_data, outfile, indent=4)

    def load_canvas(self, scene, filename):
        # Clear the current canvas
        scene.clear()
        
        with open(filename, 'r') as infile:
            items_data = json.load(infile)
        
        for item_data in items_data:
            if item_data['type'] == 'DraggableTextItem':
                # Recreate DraggableTextItem and configure its properties
                item = DraggableTextItem()
                item.textItem.setPlainText(item_data['text'])
                item.setPos(QPointF(item_data['x'], item_data['y']))
                
                # Ensure the text width and item size are correctly set
                item.setRect(0, 0, item_data['width'], item_data['height'])
                item.textItem.setTextWidth(item_data['width'])  # Adjust text width to prevent wrapping
                
                # Add the recreated item to the scene
                scene.addItem(item)

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
