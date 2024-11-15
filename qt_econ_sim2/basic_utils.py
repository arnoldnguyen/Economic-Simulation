import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QTextEdit, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal, QTimer

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

class comboBox(QWidget):

    changed_pursued = pyqtSignal(int)
    changed_mode = pyqtSignal(int)
    
    def __init__(self, items_arr, choice_levels, window):
        super().__init__()
        self.boxes = []
        self.boxes_text = [[], []]
        self.visibility_arr = []

        self.pursued_id = -1
        self.mode = -1

        for i in range(choice_levels):
            self.boxes.append(QComboBox(parent = window))
            self.boxes[-1].setVisible(False)
            self.visibility_arr.append(False)
                        
            for item in items_arr[i]:
                self.boxes_text[-1].append(item)
                self.boxes[-1].addItems(self.boxes_text[-1])

        self.boxes[0].activated.connect(lambda index : self.update_pursued_id(int(index)))
        self.boxes[1].activated.connect(lambda index : self.update_mode(int(index)))

    def init_level(self, items_arr, choice_level, size):
        print(f"at init lvl args: items {items_arr} c lvl: {choice_level} size: {size}")
        self.boxes_text[choice_level] = []
        self.boxes[choice_level].clear()
        
        for i in range(size):
            print(f"inside init lvl: items_arr: {items_arr}")
            
            #for item in items_arr:
            self.boxes_text[choice_level].append(items_arr)
            
            print(f"BOXES TEXT: {self.boxes_text} AT CHOICE LEVEL: {self.boxes_text[choice_level]}")
        
        # FIRST BUTTON, ONLY HAS 1 POSSIBLE TEXT SELECTION
        if choice_level == 0:
            self.boxes[choice_level].addItems(self.boxes_text[choice_level][0])
        else: 
            if self.pursued_id == -1:
                print("somethings off")
                self.boxes[choice_level].addItems(self.boxes_text[choice_level][0])
            else:
                show_index = self.boxes[choice_level].findText(str(self.pursued_id))
                if show_index == -1:
                    print("somethings off 2.0")
                    self.boxes[choice_level].addItems(self.boxes_text[choice_level][0])
                else:
                    self.boxes[choice_level].addItems(self.boxes_text[choice_level][show_index])
                

        print(f"fin init lvl")


    def update_choices(self, items_arr, choice_level, str_index, visibility = "NA", clear = 1):
        index = 0
        if choice_level != 0:
            index = self.boxes[choice_level-1].findText(str_index)
            if index == -1:
                print("index in update choices is messed up")
                return

        if clear:
            self.boxes_text[choice_level][index] = items_arr

            self.boxes[choice_level].clear()
            self.boxes[choice_level].addItems(self.boxes_text[index])

        else: 
            if type(items_arr) == list:

                for i in items_arr:
                    tmp_arr = self.boxes_text[choice_level][index].copy()
                    print(f"TMP ARR: {tmp_arr}")
                    tmp_arr.append(i)
                    self.boxes_text[choice_level][index] = tmp_arr

                self.boxes[choice_level].clear()
                self.boxes[choice_level].addItems(self.boxes_text[choice_level][index])

            else:
                self.boxes_text[index].append(items_arr)

                self.boxes[choice_level].clear()
                self.boxes[choice_level].addItem(items_arr)

        if visibility == "NA":
            #print(f"Branch 1: Curr V: {self.visibility_arr[choice_level]}")
            self.boxes[choice_level].setVisible(self.visibility_arr[choice_level])
        
        else:
            if visibility == "True":
                #print(f"Branch 2")
                self.visibility_arr[choice_level] = True
                self.boxes[choice_level].setVisible(True)
            else:
                #print(f"Branch 3")
                self.visibility_arr[choice_level] = False
                self.boxes[choice_level].setVisible(False)

    def wrap_visible(self, new_visibility, choice_level):
        #print(f"NV: {new_visibility}, CL: {choice_level}")
        self.visibility_arr[choice_level] = new_visibility
        self.boxes[choice_level].setVisible(self.visibility_arr[choice_level])

    def update_pursued_id(self, index):
        print(f"from combobox: updating partner: {index} type: {type(index)}")

        new_partner_str = self.boxes[0].itemText(index)

        if new_partner_str != "Wait For Next Round" and new_partner_str != "":

            try:
                self.pursued_id = int(new_partner_str)
            except ValueError:
                print("damn")

            self.wrap_visible(True, 1)
            self.boxes[1].clear()
            self.boxes[1].addItems(self.boxes_text[1][index])

        self.changed_pursued.emit(self.pursued_id)

    def update_mode(self, index):
        print("from combobox: in update mode")
        
        selected = self.boxes[1].itemText(index)
        print(f"selected: {selected}")
        
        if selected == "PROPOSE TRADE":
            print(f"in propose trade cond.")
            self.mode = 1

        elif selected == "SEND MESSAGE":
            print(f"in send message cond.")
            self.mode = 2

        elif selected == "ACCEPT REQUEST":
            print(f"in accept request cond from id: {self.pursued_id}")
            self.mode = 3
    
        print(f"Resulting mode: {self.mode}")
        self.changed_mode.emit(self.mode)


# HANDLE TIMER & TIMER LABEL
# _________________________________________________________________________________________________________________________
class timeSystem(QWidget):
    time_up = pyqtSignal()

    def __init__(self, window, length):
        super().__init__()
        self.time_left = length

        self.label = QLabel(f"Time left: {self.time_left} seconds", parent=window)
        self.label.setVisible(False)
        
        self.timer = QTimer()
        self.timer.setInterval(1000)  # Set timer interval to 1 second
        
        self.timer.timeout.connect(self.update_timer)
    
    def update_timer(self):
        print("updating the time metric")
        self.time_left -= 1

        if self.time_left == 0: 
            print("Times Up")
            self.timer.stop()
            self.time_up.emit()

        self.label.setText(f"Time left: {self.time_left} seconds")
# _________________________________________________________________________________________________________________________
