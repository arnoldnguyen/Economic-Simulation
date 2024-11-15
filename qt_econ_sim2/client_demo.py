import socket
import sys
import threading

import numpy
import pandas
import matplotlib
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy, QTextEdit, QListWidget, QComboBox
from PyQt5.QtCore import pyqtSignal, Qt, QMetaObject, Q_ARG

from PyQt5.QtGui import QFont

from basic_utils import textBox, scrollableBox, comboBox, timeSystem

from global_functions import *

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

pursued_id = -1

partner_id = -1

'''
MODE:
0 IS NOTHING
1 IS PROPOSE TRADE
2 IS SEND MESSAGE
3 IS ACCEPT
'''

mode = 0

def start_client(server_listener_args):
    # HANDLE SOCKET CONNECTION
    print(f"Connecting to Server Host: {CLIENT_HOST} at Port: {PORT}")
    # _________________________________________________________________________________________________________________________ 
    client_socket.connect((CLIENT_HOST, PORT))
    print("Connection Sucessfull")
    threading.Thread(target=server_listener, args=[server_listener_args], daemon=True).start()
    # _________________________________________________________________________________________________________________________

def get_pursued_id(new_id):
    global pursued_id
    pursued_id = new_id

def get_mode(new_mode, transmit_data_args):
    global mode
    mode = new_mode
    print(f"in client: new mode: {new_mode} should equal mode: {mode}")

    if mode == 1: 
        transmit_data("", transmit_data_args)

    if mode == 3:
        print(f"In client mode = 3 accept from pursued {pursued_id}")
        client_socket.send(f"ACCEPT REQUEST FROM:{pursued_id}".encode('utf-8'))

def transmit_data(text, transmit_data_args):
    global pursued_id, mode
    server_scrollable = transmit_data_args[1]
    input_box = transmit_data_args[0]
    # HANLDE TRANSMISION
    # _________________________________________________________________________________________________________________________
    print(f"Current mode: {mode}, with text: {text}")
    if mode == 0:
        QMetaObject.invokeMethod(
            server_scrollable.textEdit, 
            "append", 
            Qt.QueuedConnection, 
            Q_ARG(str, f"No action selected")
        )

        return
    
    elif mode == 1: # PROPOSE TRADE
        print(f"Trade Id: {pursued_id}")
        input_box.textEdit.append(f"You requested to trade with {pursued_id}") 
        client_socket.send(f"PROPOSE TRADE:{pursued_id}".encode('utf-8'))
    
    elif mode == 2:
        input_box.textEdit.append(f"SENT: {text}") 
        client_socket.send(f"MSSG:{pursued_id};{text}".encode('utf-8'))

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
    partner_list_widget = server_listener_args[5]
    choice_box = server_listener_args[6]
    time_system = server_listener_args[7]
    send_label = server_listener_args[8]

    while True: 
        try:
            server_response = client_socket.recv(1024).decode('utf-8')
            if server_response:
                server_response = server_response.split(';')
                print(server_response)
                for response in server_response:
                    #print(f"Server response: {response}")
                    print(f"Server Response: {response}")
                    if response == "":
                        continue

                    elif response[:len("TIME UP")] == "TIME UP":
                        continue


                    elif response[:len("PARTNER ID SET:")] == "PARTNER ID SET:":
                        print(f"set partner id to {response.split(':')[1]}")
                        partner_id = response.split(":")[1]

                        QMetaObject.invokeMethod(
                            send_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"send to partner: {partner_id}")
                        )

                        QMetaObject.invokeMethod(
                            box.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"Your partner is now {partner_id}")
                        )



                    elif response[:len("MSSG:")] == "MSSG:":
                        response = response.split(":")[1]
                        trader_id = response.split(",")[0]
                        mssg = response.split(",")[1]
                        print(f"got message: {mssg} from {trader_id}")

                        QMetaObject.invokeMethod(
                            box.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"FROM {trader_id}: {mssg}")
                        )


                    elif response[:len("INIT REQUEST")] == "INIT REQUEST":
                        print("handle init request")
                            
                        sender_id = response.split(":")[1]

                        choice_box.update_choices([f"ACCEPT REQUEST"], 1, str(sender_id), clear = 0), 

                        QMetaObject.invokeMethod(
                            box.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"{sender_id} would like to trade with you!")
                        )


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
                    elif response == "You Are Connected To The Server":
                        print("change status label")
                        QMetaObject.invokeMethod(
                            connection_status_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, "Simulation has started")
                        )

                    elif response[:11] == "Partner ID:":
                        print("changed partner")
                        pursued_id = int(response.split(":")[1])
                        QMetaObject.invokeMethod(
                            message_log_label, 
                            "setText", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"Message Log To {pursued_id}")
                        )

                    elif response[:len("Player List:")] == "Player List:":
                        
                        print("caught list")
                        
                        if response.split(":")[1] == "":
                            QMetaObject.invokeMethod(
                                    partner_list.textEdit, 
                                    "setText", 
                                    Qt.QueuedConnection, 
                                    Q_ARG(str, "No Possible Partners This Round")
                                )
                                
                        else:
                            QMetaObject.invokeMethod(
                                partner_list.textEdit, 
                                "setText", 
                                Qt.QueuedConnection, 
                                Q_ARG(str, response.split(":")[1])
                            )
                        
                        numbers_array = response.split(":")[1].split('\n')

                        if numbers_array[0] == "":
                            choice_box.blockSignals(True)
                            choice_box.init_level(["Wait For Next Round"], 0, 1)
                            choice_box.blockSignals(False)

                            choice_box.wrap_visible(False, 1)
                        
                        else:
                            choice_box.blockSignals(True)
                            print("At first init")
                            choice_box.init_level(numbers_array, 0, 1)
                            print("at second init")
                            second_choices = ["PROPOSE TRADE", "SEND MESSAGE"]
                            #choice_box.update_choices(second_choices, 1, resize=len(numbers_array))
                            choice_box.init_level(second_choices, 1, len(numbers_array))
                            print("done with init")

                            choice_box.blockSignals(False)
                            choice_box.wrap_visible(False, 1)

                        QMetaObject.invokeMethod(
                            time_system.timer, 
                            "start", 
                            Qt.QueuedConnection, 
                        )

                        time_system.label.setVisible(True)
    
                    else: 
                        print("EDIT BOX")
                        QMetaObject.invokeMethod(
                            box.textEdit, 
                            "append", 
                            Qt.QueuedConnection, 
                            Q_ARG(str, f"FROM: {response}")
                        )


                    #receive_label.setText("Last Message: " + response)
                
        except Exception as e:
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

    time_system = timeSystem(window, 30)
    ui_grid(time_system.label, pos=(2, 1))

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

    scrollable_text = scrollableBox(window)
    ui_grid(scrollable_text.textEdit, pos=(1, 5), size=(2, 7), margin=(10, 10))

    players_label = QLabel("Players", parent=window)
    players_label.setAlignment(Qt.AlignCenter)
    ui_grid(players_label, pos=(3, 4))
    
    players_list = scrollableBox(window)
    players_list.textEdit.setText("No Players Yet")
    ui_grid(players_list.textEdit, pos=(3, 5), size=(3, 7), margin=(10, 10))

    send_to_server_label = QLabel("Send To Server", parent=window)
    send_to_server_label.setAlignment(Qt.AlignCenter)
    ui_grid(send_to_server_label, pos=(0, 4))

    send_to_server_box = textBox(window)
    ui_grid(send_to_server_box.textbox, pos=(3, 2), area=(150, 30))

    server_scrollable = scrollableBox(window)
    ui_grid(server_scrollable.textEdit, pos=(0, 5), size=(0, 7), margin=(10, 10))

    partner_list_widget = QListWidget(parent = window)
    ui_grid(partner_list_widget, pos=(4, 5))

    transmit_data_args = [scrollable_text, server_scrollable]

    items_arr = [["Waiting For Server To Start"], ["PROPOSE TRADE", "SEND MESSAGE"]]
    choice_box = comboBox(items_arr, 2, window)
    choice_box.changed_pursued.connect(get_pursued_id)
    choice_box.changed_mode.connect(lambda new_mode: get_mode(new_mode, transmit_data_args))

    server_listener_args = [scrollable_text, connection_status_label, receive_label, players_list, server_scrollable, partner_list_widget, choice_box, time_system, send_label]

    ui_grid(choice_box.boxes[0], pos=(1, 9))
    ui_grid(choice_box.boxes[1], pos=(2, 9))

    choice_box.boxes[0].setStyleSheet("""
        QComboBox {
            text-align: center;
        }
        QComboBox QAbstractItemView {
            text-align: center;
        }
    """)

    choice_box.boxes[1].setStyleSheet("""
        QComboBox {
            text-align: center;
        }
        QComboBox QAbstractItemView {
            text-align: center;
        }
    """)

    choice_box.wrap_visible(True, 0)
    choice_box.wrap_visible(False, 1)


    start_client(server_listener_args)

    # _________________________________________________________________________________________________________________________

    # DEFINE SIGNAL HANDLERS
    # _________________________________________________________________________________________________________________________
    # TRANSMIT DATA CALLER
    #send_message_box.text_saved.connect(lambda text: transmit_data(f"TRADE REQUEST:{pursued_id};" + text, transmit_data_args))
    
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
