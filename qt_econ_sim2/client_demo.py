import socket
import sys
import threading

import numpy
import pandas
import matplotlib
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt, QMetaObject, Q_ARG

from PyQt5.QtGui import QFont

from basic_utils import textBox, scrollableBox

from global_functions import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

partner_id = -1

def start_client(server_listener_args):
    # HANDLE SOCKET CONNECTION
    print(f"Connecting to Server Host: {CLIENT_HOST} at Port: {PORT}")
    # _________________________________________________________________________________________________________________________ 
    client_socket.connect((CLIENT_HOST, PORT))
    print("Connection Sucessfull")
    threading.Thread(target=server_listener, args=[server_listener_args], daemon=True).start()
    # _________________________________________________________________________________________________________________________

def transmit_data(text, transmit_data_args):
    # HANLDE TRANSMISION
    # _________________________________________________________________________________________________________________________
    input_box = transmit_data_args[0]

    input_box.textEdit.append(f"SENT: {text}") 
    client_socket.send(text.encode('utf-8'))
    # _________________________________________________________________________________________________________________________

# MANUALY CLOSE THE CONNECTION FROM CLIENT SIDE
def close_connection():
    client_socket.send("Connection Over".encode('utf-8'))
    client_socket.close()

# HANDLE RECEPTION
def server_listener(server_listener_args):
    
    box = server_listener_args[0]
    connection_status_label = server_listener_args[1]
    message_log_label = server_listener_args[2]
    partner_list = server_listener_args[3]
    server_scrollable = server_listener_args[4]

    while True: 
        try:
            server_response = client_socket.recv(1024).decode('utf-8')
            if server_response:
                server_response = server_response.split(';')
                
                for response in server_response:
                    #print(f"Server response: {response}")
                    print(f"Server Response: {response}")
                    if response == "":
                        continue
                    
                    elif response[:len("PARTNER LEFT")] == "PARTNER LEFT":
                        print("handle partner leaving")
                        QMetaObject.invokeMethod(
                            server_scrollable.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"Negotiation has broken down. Partner has left")
                        )

                        QMetaObject.invokeMethod(
                            message_log_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"No Partner Currently")
                        )

                    elif response[:len("SWITCH PARTNER:")] == "SWITCH PARTNER:":
                        print("switch partner")
                        QMetaObject.invokeMethod(
                            server_scrollable.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"{response.split(':')[1]} would like to trade with you! Type: Y: {response.split(':')[1]} to Accept or N: {response.split(':')[1]} to Reject")
                        )

                    elif response == "You Are Connected To The Server":
                        print("change status label")
                        QMetaObject.invokeMethod(
                            connection_status_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, "Simulation has started")
                        )

                    elif response[:11] == "Partner ID:":
                        print("changed")
                        partner_id = int(response.split(":")[1])
                        QMetaObject.invokeMethod(
                            message_log_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"Message Log To {partner_id}")
                        )

                    elif response[:len("Player List:")] == "Player List:":
                        print("caught list")
                        QMetaObject.invokeMethod(
                            partner_list.textEdit, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, response.split(":")[1])
                        )

                    else: 
                        print("EDIT BOX")
                        QMetaObject.invokeMethod(
                            box.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"FROM: {response}")
                        )
                    #receive_label.setText("Last Message: " + response)
                
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

    #print("1")
    # CREATE A LABEL
    send_label = QLabel('Send to Partner', parent=window)
    send_label.setAlignment(Qt.AlignCenter)
    ui_grid(send_label, pos=(1, 1))

    connection_status_label = QLabel("Waiting For Server To Start Simulation", parent=window)
    connection_status_label.setAlignment(Qt.AlignCenter)
    ui_grid(connection_status_label, pos=(2, 0), size=(3, 0))

    #print("2")
    # CREATE A TEXTBOX
    send_message_box = textBox(window)
    ui_grid(send_message_box.textbox, pos=(1, 2), area=(150, 30))
    
    #print("3")
    # CREATE CLOSE CONNECTION BUTTON
    kill_sock_button = QPushButton("End Connection", parent=window)
    ui_grid(kill_sock_button, pos=(1, 3), area=(150, 30))

    #print("4")
    # CREATE A LABEL
    receive_label = QLabel("Message Log", parent=window)
    receive_label.setAlignment(Qt.AlignCenter)
    ui_grid(receive_label, pos=(1, 4), size=(2, 4))

    print("5")
    scrollable_text = scrollableBox(window)
    ui_grid(scrollable_text.textEdit, pos=(1, 5), size=(2, 13), margin=(10, 10))

    players_label = QLabel("Players", parent=window)
    players_label.setAlignment(Qt.AlignCenter)
    ui_grid(players_label, pos=(3, 4))
    
    players_list = scrollableBox(window)
    players_list.textEdit.setText("No Players Yet")
    ui_grid(players_list.textEdit, pos=(3, 5), size=(3, 13), margin=(10, 10))

    send_to_server_label = QLabel("Send To Server", parent=window)
    send_to_server_label.setAlignment(Qt.AlignCenter)
    ui_grid(send_to_server_label, pos=(0, 4))

    send_to_server_box = textBox(window)
    ui_grid(send_to_server_box.textbox, pos=(3, 2), area=(150, 30))

    server_scrollable = scrollableBox(window)
    ui_grid(server_scrollable.textEdit, pos=(0, 5), size=(0, 13), margin=(10, 10))

    transmit_data_args = [scrollable_text]
    server_listener_args = [scrollable_text, connection_status_label, receive_label, players_list, server_scrollable]

    start_client(server_listener_args)
    # _________________________________________________________________________________________________________________________

    # DEFINE SIGNAL HANDLERS
    # _________________________________________________________________________________________________________________________
    # TRANSMIT DATA CALLER
    send_message_box.text_saved.connect(lambda text: transmit_data(text, transmit_data_args))
    
    send_to_server_box.text_saved.connect(lambda text: client_socket.send(f"SERVER:{text}".encode('utf-8')))

    # END CONNECTION CALLER
    kill_sock_button.clicked.connect(close_connection)



    # ...


    # _________________________________________________________________________________________________________________________

    # RENDER AND START EVENT LOOP
    # _________________________________________________________________________________________________________________________
    #window.setLayout(layout)
    print("ASDASD")
    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())
    # _________________________________________________________________________________________________________________________