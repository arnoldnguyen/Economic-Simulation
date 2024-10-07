import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QTextEdit, QPushButton
from PyQt5.QtCore import pyqtSignal

class textBox(QWidget):
    # EMIT SAVED STRING TO MAIN WINDOW
    text_saved = pyqtSignal(str)  # Create a custom signal

    def __init__(self, window):
        # INITIALIZE THE TEXT BOX
        # _________________________________________________________________________________________________________________________
        super().__init__()
        # BUILD TEXTBOX
        self.textbox = QLineEdit(self)
        self.textbox.setPlaceholderText("Enter text here")
        self.textbox.setParent(window)
        self.save_text = ""

        # SET UP CONNECTION WITH SAVE TEXT METHOD (TRIGGERS WHEN "RETURN" IS HIT)
        # _________________________________________________________________________________________________________________________
        self.textbox.returnPressed.connect(self.emit_text)
        # _________________________________________________________________________________________________________________________
    def emit_text(self):
        # EMIT TEXT TO CLASS SIGNAL
        self.text_saved.emit(self.textbox.text())
        # CLEAR TEXTBOX
        self.textbox.clear()


class scrollableBox(QWidget):
    signal = pyqtSignal(str)  # Create a custom signal
    def __init__(self, window):
        # INITIALIZE THE TEXT BOX
        # _________________________________________________________________________________________________________________________
        super().__init__()
        self.textEdit = QTextEdit()
        self.textEdit.setText("")
        self.textEdit.setReadOnly(True)  # Set to read-only if you don't want editing
        self.textEdit.setParent(window)

class pushButton(QWidget):
    signal = pyqtSignal()
    def __init__(self, name, window):
        super().__init__()
        self.button = QPushButton(name, parent=window)
