import socket
import sys
import threading
import queue

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

from global_functions import *
from basic_utils import textBox, scrollableBox, pushButton

# _________________________________________________________________________________________________________________________
# PAIRING QUEUE
client_queue = queue.Queue()
queue_lock = threading.Lock()


# HAHSMAP: CLIENT ADDRESS -> IF IT IS PAIRED, PARTNER ADDRESS ELSE NONE
pair_map = {}
# _________________________________________________________________________________________________________________________

# HAHSMAP: CLIENT ADDRESS -> CLIENT SOCKET
client_map = {}
# PUBLIC RESOURCE, NEED TO LOCK TO AVOID RACE CONDITIONS
client_map_lock = threading.Lock()

def handle_single_client(client_socket, addr):
    with client_map_lock:
        client_map[addr] = client_socket  # Add the client to the dictionary

    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                
                # IF THE CLIENT IS NOT PAIRED, SEND MESSAGE TO SERVER
                if pair_map[addr] == None:
                    print(f"Message from {addr} to Server: \n\"{message}\"")
            
                # ELSE SEND MESSAGE TO PARTNER
                else:
                    print(f"Message from {addr}: {message} to {pair_map[addr]}")
                    client_map[pair_map[addr]].send(message.encode('utf-8'))

            else:
                print(f"{addr} disconnected.")
                break

    except Exception as e:
        print(f"Error with {addr}: {e}")
    
    finally:
        client_socket.close()

        # MAYBE NEED TO DEL THE CLIENT PAIR_MAP AND CLIENT_QUEUE INDEXES TOO ???
        del client_map[addr]  # Remove client from dictionary
        
        print(f"Connection closed with {addr}")

def server_thread(server_socket, q_signal, p_signal):
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected to {client_socket} from {addr}")
        
        client_queue.put((client_socket, addr))
        pair_map[addr] = None

        single_client_handler = threading.Thread(target=handle_single_client, args=(client_socket, addr))
        single_client_handler.start()
        
        queue_list = list(client_queue.queue)
        queue_string = ""
             
        for i in queue_list:
            client, addr = i
            queue_string += f"{addr}\n"
        
        q_signal.emit(queue_string)

def start_match(q_signal, p_signal):

    print()
    print("yer")
    print()
    
    with queue_lock:
        # If two clients are in the queue, pair them together
        while client_queue.qsize() >= 2:
            client1, addr1 = client_queue.get()
            client2, addr2 = client_queue.get()
            
            pair_map[addr1] = addr2
            pair_map[addr2] = addr1

            p_signal.emit(f"{addr1[0]}, {addr1[1]} is connected to {addr2[0]}, {addr2[1]}")

        queue_list = list(client_queue.queue)
        queue_string = ""
                
        for i in queue_list:
            client, addr = i
            queue_string += f"{addr}\n"
        
        q_signal.emit(queue_string)

def start_server():
    
    app = QApplication(sys.argv)
    # BUILD THE WINDOW
    window = QWidget()
    window.setWindowTitle('Hello, PyQt!')
    window.setGeometry(100, 100, WIDTH, HEIGHT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket options to reuse the address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((HOST, PORT))
    
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    queue_label = QLabel('Queue Dashboard', parent=window)
    queue_label.setAlignment(Qt.AlignCenter)
    ui_grid(queue_label, pos=(1, 3))

    queue_box = scrollableBox(window)
    ui_grid(queue_box.textEdit, pos=(1, 4), size=(1, 9), margin=(10, 10))
    queue_box.signal.connect(lambda text: queue_box.textEdit.setText(text))

    pair_label = QLabel('Pair Dashboard', parent=window)
    pair_label.setAlignment(Qt.AlignCenter)
    ui_grid(pair_label, pos=(2, 3), size=(3, 3))

    pair_box = scrollableBox(window)
    ui_grid(pair_box.textEdit, pos=(2, 4), size=(3, 9), margin=(10, 10))
    pair_box.signal.connect(lambda text: pair_box.textEdit.append(text))

    start_match_button = pushButton("Start Match", window)
    ui_grid(start_match_button.button, pos=(0, 4), margin=(10, 10))
    start_match_button.button.clicked.connect(lambda: start_match(queue_box.signal,pair_box.signal))

    
    params = [
        ('Number of Buyers', 'num_buyers', 10),
        ('Number of Sellers', 'num_sellers', 10),
        ('Buyer Lower Bound', 'buyer_lower_bound', 5),
        ('Buyer Upper Bound', 'buyer_upper_bound', 10),
        ('Seller Lower Bound', 'seller_lower_bound', 0),
        ('Seller Upper Bound', 'seller_upper_bound', 15),
        ('Lambda Value', 'lambda', 0.1),
        ('Gamma Value', 'gamma', 0.05),
        ('d Value', 'dValue', 0),
        ('p Value', 'pValue', 1),
        ('Kappa Value', 'kapValue', 1),
        ('Fixed Cost', 'fixedCost', 0.4),
        ('Number of Steps', 'num_steps', 10),
        ('Number of Human\nPlayers', 'human_players', 1)
        #('Human Roles (comma-separated buyer/seller)', 'human_roles', 'buyer'),
        #('Human Initial Values (comma-separated)', 'human_initial_values', '7.5'),
        #('Human Offer Prices (comma-separated)', 'human_offer_prices', '6'),
        #('Human Costs (comma-separated)', 'human_costs', '7.5')
    ]


    # THESE BUTTONS ARE NOT CONNECTED TO ANY VARIABLES. 
    # IM NOT REALLY SURE HOW THEY'RE SUPPOSED TO WORK, SO IDK HOW TO PROCEED FROM HERE.

    params_buttons = []

    params_text_boxes = []

    for index, (i, j, k) in enumerate(params):
        params_buttons.append(pushButton(i, window))
        ui_grid(params_buttons[-1].button, pos=(1 + index // 4, 11 + (index % 4)), margin=(30, 0), font_size = 10)

        params_text_boxes.append(textBox(window))
        params_text_boxes[-1].textbox.setText(str(k))
        ui_grid(params_text_boxes[-1].textbox, pos=(1 + index // 4, 11 + (index % 4)), margin=(115, 0), font_size = 10, allign="r")



    server_thread_handler = threading.Thread(target=server_thread, args=(server_socket, queue_box.signal, pair_box.signal))
    server_thread_handler.start()



    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_server()
