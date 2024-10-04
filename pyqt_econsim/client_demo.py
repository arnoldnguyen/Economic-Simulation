import socket
import sys
import threading

import numpy
import pandas
import matplotlib
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from basic_utils import textBox, scrollableBox

from global_functions import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def start_client(box):
    # HANDLE SOCKET CONNECTION
    # _________________________________________________________________________________________________________________________        
    client_socket.connect((HOST, PORT))
    threading.Thread(target=server_listener, args=[box], daemon=True).start()
    # _________________________________________________________________________________________________________________________

def transmit_data(text, box):
    # HANLDE TRANSMISION
    # _________________________________________________________________________________________________________________________
    box.textEdit.append(f"SENT: {text}") 
    client_socket.send(text.encode('utf-8'))
    # _________________________________________________________________________________________________________________________

# MANUALY CLOSE THE CONNECTION FROM CLIENT SIDE
def close_connection():
    client_socket.send("Connection Over".encode('utf-8'))
    client_socket.close()

# HANDLE RECEPTION
def server_listener(box):
    while True: 
        try:
            server_response = client_socket.recv(1024).decode('utf-8')
            if server_response:
                #print(f"Server response: {server_response}")
                print(server_response)
                box.textEdit.append(f"FROM: {server_response}")
                #receive_label.setText("Last Message: " + server_response)
                
        except:
            print(f"Error receiving message: {e}")
            break

if __name__ == "__main__":
    # INITIAL SETUP
    # _________________________________________________________________________________________________________________________
    # BUILD THE APP
    app = QApplication(sys.argv)

    # BUILD THE WINDOW
    window = QWidget()
    window.setWindowTitle('Hello, PyQt!')
    window.setGeometry(100, 100, WIDTH, HEIGHT)

    # CREATE A LABEL
    send_label = QLabel('Send to Server!', parent=window)
    send_label.setAlignment(Qt.AlignCenter)

    ui_grid(send_label, pos=(1, 0), size=(3, 0))

    # CREATE A TEXTBOX
    textBox = textBox(window)
    ui_grid(textBox.textbox, pos=(1, 1), size=(3, 1), area=(150, 30))
    
    # CREATE CLOSE CONNECTION BUTTON
    kill_sock_button = QPushButton("End Connection", parent=window)
    ui_grid(kill_sock_button, pos=(1, 2), size=(3, 1), area=(150, 30))

    # CREATE A LABEL
    receive_label = QLabel("Message Log", parent=window)
    receive_label.setAlignment(Qt.AlignCenter)
    ui_grid(receive_label, pos=(1, 3), size=(3, 1))


    scrollable_text = scrollableBox(window)
    ui_grid(scrollable_text.textEdit, pos=(1, 4), size=(3, 9))

    start_client(scrollable_text)
    # _________________________________________________________________________________________________________________________

    # DEFINE SIGNAL HANDLERS
    # _________________________________________________________________________________________________________________________
    # TRANSMIT DATA CALLER
    textBox.text_saved.connect(lambda text: transmit_data(text, scrollable_text))
    
    # END CONNECTION CALLER
    kill_sock_button.clicked.connect(close_connection)


    # ...


    # _________________________________________________________________________________________________________________________

    # RENDER AND START EVENT LOOP
    # _________________________________________________________________________________________________________________________
    #window.setLayout(layout)

    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())
    # _________________________________________________________________________________________________________________________