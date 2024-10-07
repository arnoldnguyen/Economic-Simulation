# server_demo.py

import socket
import sys
import threading
import queue

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

# Import the agent classes from Agents.py
from Agents import Agent, MarketAgent, MarketSeller, MarketBuyer, HumanPlayer

# Import custom utilities (assuming these are custom modules you have)
# If these modules are not available, you'll need to provide them or adjust the code accordingly.
# For the purpose of this code, I'll define placeholder functions/classes.
try:
    from global_functions import *
    from basic_utils import textBox, scrollableBox, pushButton
except ImportError:
    # Placeholder definitions for missing modules
    def ui_grid(widget, pos=(0, 0), size=(1, 1), margin=(0, 0), font_size=12, allign="l"):
        pass

    class textBox:
        def __init__(self, parent=None):
            self.textbox = QLabel(parent)

    class scrollableBox:
        signal = pyqtSignal(str)

        def __init__(self, parent=None):
            self.textEdit = QLabel(parent)

    class pushButton:
        def __init__(self, label, parent=None):
            self.button = QPushButton(label, parent)

# Define constants
HOST = 'localhost'
PORT = 12345
WIDTH = 800
HEIGHT = 600

# _________________________________________________________________________________________________________________________
# PAIRING QUEUE
client_queue = queue.Queue()
queue_lock = threading.Lock()

# HAHSMAP: CLIENT ADDRESS -> IF IT IS PAIRED, PARTNER ADDRESS ELSE NONE
pair_map = {}
# _________________________________________________________________________________________________________________________

# HAHSMAP: CLIENT ADDRESS -> CLIENT SOCKET
# PUBLIC RESOURCE, NEED TO LOCK TO AVOID RACE CONDITIONS
client_map = {}
client_map_lock = threading.Lock()

# QUEUES FOR BUYERS AND SELLERS
buyer_queue = queue.Queue()
seller_queue = queue.Queue()

# DICTIONARY TO STORE CLIENT DATA
# KEY: CLIENT ADDRESS
# VALUE: DICTIONARY WITH ROLE, SOCKET, OFFER_PRICE, PARTNER_SOCKET, PARTNER_ADDR
client_data = {}

def handle_single_client(client_socket, addr):
    with client_map_lock:
        client_map[addr] = client_socket  # Add the client to the client map

    role = None

    try:
        # First message should be the role
        initial_message = client_socket.recv(1024).decode('utf-8')
        if initial_message.startswith('ROLE:'):
            role = initial_message.split(':')[1]
            if role == 'buyer':
                buyer_queue.put((client_socket, addr))
            elif role == 'seller':
                seller_queue.put((client_socket, addr))
            else:
                client_socket.send('INVALID_ROLE'.encode('utf-8'))
                client_socket.close()
                return

            pair_clients()  # Attempt to pair clients

        else:
            client_socket.send('NO_ROLE_PROVIDED'.encode('utf-8'))
            client_socket.close()
            return

        # Now handle messages from the client
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith('OFFER_PRICE:'):
                offer_price = float(message.split(':')[1])
                # Store the offer price
                client_data[addr]['offer_price'] = offer_price
                check_trade(client_data[addr])
            else:
                print(f"Unknown message from {addr}: {message}")

    except Exception as e:
        print(f"Error with {addr}: {e}")

    finally:
        client_socket.close()
        with client_map_lock:
            if addr in client_map:
                del client_map[addr]
        print(f"Connection closed with {addr}")

def pair_clients():
    # If both queues have clients, pair them together
    while not buyer_queue.empty() and not seller_queue.empty():
        client_socket_buyer, addr_buyer = buyer_queue.get()
        client_socket_seller, addr_seller = seller_queue.get()

        # Update client_data
        client_data[addr_buyer] = {
            'role': 'buyer',
            'socket': client_socket_buyer,
            'offer_price': None,
            'partner_socket': client_socket_seller,
            'partner_addr': addr_seller
        }

        client_data[addr_seller] = {
            'role': 'seller',
            'socket': client_socket_seller,
            'offer_price': None,
            'partner_socket': client_socket_buyer,
            'partner_addr': addr_buyer
        }

        # Notify clients that they have been paired (optional)
        client_socket_buyer.send('PAIRED_WITH_SELLER'.encode('utf-8'))
        client_socket_seller.send('PAIRED_WITH_BUYER'.encode('utf-8'))

def check_trade(client_info):
    addr = client_info['socket'].getpeername()
    partner_addr = client_info['partner_addr']
    partner_info = client_data.get(partner_addr)

    # Check if both clients have submitted their offer prices
    if client_info['offer_price'] is not None and partner_info and partner_info['offer_price'] is not None:
        buyer_price = client_info['offer_price'] if client_info['role'] == 'buyer' else partner_info['offer_price']
        seller_price = client_info['offer_price'] if client_info['role'] == 'seller' else partner_info['offer_price']

        # Determine if trade is successful
        if buyer_price >= seller_price:
            result = f"Trade Successful! Buyer offered {buyer_price}, Seller asked {seller_price}."
        else:
            result = f"Trade Failed. Buyer offered {buyer_price}, Seller asked {seller_price}."

        # Send result to both clients
        client_info['socket'].send(f"TRADE_RESULT:{result}".encode('utf-8'))
        partner_info['socket'].send(f"TRADE_RESULT:{result}".encode('utf-8'))

        # Reset offer prices for next trade
        client_info['offer_price'] = None
        partner_info['offer_price'] = None

        # Re-queue clients for another trade
        if client_info['role'] == 'buyer':
            buyer_queue.put((client_info['socket'], addr))
        else:
            seller_queue.put((client_info['socket'], addr))

        pair_clients()  # Attempt to pair clients again

def server_thread(server_socket, q_signal, p_signal):
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected to {addr}")

        # Add client to queue and pair map
        client_queue.put((client_socket, addr))
        pair_map[addr] = None

        single_client_handler = threading.Thread(target=handle_single_client, args=(client_socket, addr))
        single_client_handler.start()

        # Update queue display in GUI
        queue_list = list(client_queue.queue)
        queue_string = ""

        for i in queue_list:
            client, addr = i
            queue_string += f"{addr}\n"

        q_signal.emit(queue_string)

def start_match(q_signal, p_signal):
    # Start matching clients from the queue
    with queue_lock:
        while client_queue.qsize() >= 2:
            client1, addr1 = client_queue.get()
            client2, addr2 = client_queue.get()

            # Update pair map
            pair_map[addr1] = addr2
            pair_map[addr2] = addr1

            p_signal.emit(f"{addr1[0]}, {addr1[1]} is connected to {addr2[0]}, {addr2[1]}")

        # Update queue display in GUI
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
    window.setWindowTitle('Server Dashboard')
    window.setGeometry(100, 100, WIDTH, HEIGHT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Set socket options to reuse the address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    # GUI Elements

    # Queue Dashboard
    queue_label = QLabel('Queue Dashboard', parent=window)
    queue_label.setAlignment(Qt.AlignCenter)
    ui_grid(queue_label, pos=(1, 3))

    queue_box = scrollableBox(window)
    ui_grid(queue_box.textEdit, pos=(1, 4), size=(1, 9), margin=(10, 10))
    queue_box.signal.connect(lambda text: queue_box.textEdit.setText(text))

    # Pair Dashboard
    pair_label = QLabel('Pair Dashboard', parent=window)
    pair_label.setAlignment(Qt.AlignCenter)
    ui_grid(pair_label, pos=(2, 3), size=(3, 3))

    pair_box = scrollableBox(window)
    ui_grid(pair_box.textEdit, pos=(2, 4), size=(3, 9), margin=(10, 10))
    pair_box.signal.connect(lambda text: pair_box.textEdit.append(text))

    # Start Match Button
    start_match_button = pushButton("Start Match", window)
    ui_grid(start_match_button.button, pos=(0, 4), margin=(10, 10))
    start_match_button.button.clicked.connect(lambda: start_match(queue_box.signal, pair_box.signal))

    # Parameters
    params = [
        ('Number of Buyers', 'num_buyers', 10),
        ('Number of Sellers', 'num_sellers', 10),
        ('Buyer Lower Bound', 'buyer_lower_bound', 5),
        ('Buyer Upper Bound', 'buyer_upper_bound', 10),
        ('Seller Lower Bound', 'seller_lower_bound', 0),
        ('Seller Upper Bound', 'seller_upper_bound', 15),
        ('Lambda Value', 'lambda_value', 0.1),
        ('Gamma Value', 'gamma', 0.05),
        ('d Value', 'dValue', 0),
        ('p Value', 'pValue', 1),
        ('Kappa Value', 'kapValue', 1),
        ('Fixed Cost', 'fixedCost', 0.4),
        ('Number of Steps', 'num_steps', 10),
        ('Number of Human\nPlayers', 'human_players', 1)
        # ('Human Roles (comma-separated buyer/seller)', 'human_roles', 'buyer'),
        # ('Human Initial Values (comma-separated)', 'human_initial_values', '7.5'),
        # ('Human Offer Prices (comma-separated)', 'human_offer_prices', '6'),
        # ('Human Costs (comma-separated)', 'human_costs', '7.5')
    ]

    # Initialize parameter buttons and text boxes
    params_buttons = []
    params_text_boxes = []

    for index, (label_text, param_name, default_value) in enumerate(params):
        # Parameter label/button
        params_buttons.append(pushButton(label_text, window))
        ui_grid(params_buttons[-1].button, pos=(1 + index // 4, 11 + (index % 4)), margin=(30, 0), font_size=10)

        # Parameter input textbox
        params_text_boxes.append(textBox(window))
        params_text_boxes[-1].textbox.setText(str(default_value))
        ui_grid(params_text_boxes[-1].textbox, pos=(1 + index // 4, 11 + (index % 4)), margin=(115, 0), font_size=10, allign="r")

    # Start the server thread
    server_thread_handler = threading.Thread(target=server_thread, args=(server_socket, queue_box.signal, pair_box.signal))
    server_thread_handler.daemon = True
    server_thread_handler.start()

    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_server()
