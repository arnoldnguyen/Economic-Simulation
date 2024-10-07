# server_demo.py

import socket
import sys
import threading
import queue

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QPushButton, QLineEdit, QVBoxLayout,
    QGridLayout, QTextEdit, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt, QObject
from PyQt5.QtGui import QFont, QTextOption

# Define constants
HOST = '0.0.0.0'
PORT = 12345
WIDTH = 800
HEIGHT = 600

# Locks for thread safety
client_data_lock = threading.Lock()

# Client data dictionary
# Key: Client address (tuple)
# Value: Dictionary with client information
client_data = {}

class scrollableBox(QObject):
    signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.textEdit = QTextEdit(parent)
        self.textEdit.setReadOnly(True)
        self.textEdit.setAlignment(Qt.AlignTop)
        self.textEdit.setWordWrapMode(QTextOption.WordWrap)

class pushButton:
    def __init__(self, label, parent=None):
        self.button = QPushButton(label, parent)

class textBox:
    def __init__(self, parent=None):
        self.textbox = QLineEdit(parent)

def handle_single_client(client_socket, addr, q_signal):
    role = None

    try:
        # First message should be the role
        initial_message = client_socket.recv(1024).decode('utf-8')
        if initial_message.startswith('ROLE:'):
            role = initial_message.split(':')[1]
            with client_data_lock:
                client_data[addr] = {
                    'role': role,
                    'socket': client_socket,
                    'offer_price': None,
                    'selected_partner': None,
                    'selected_by': set(),
                    'state': 'available',
                    'partner_addr': None
                }

            # Update queue display
            update_queue_display(q_signal)
            # Broadcast available partners to all clients
            broadcast_available_partners()

            while True:
                message = client_socket.recv(4096).decode('utf-8')
                if not message:
                    print(f"Client {addr} disconnected.")
                    break
                # Handle multiple messages separated by newline
                messages = message.strip().split('\n')
                for msg in messages:
                    if msg.startswith('OFFER_PRICE:'):
                        offer_price = float(msg.split(':')[1])
                        # Store the offer price
                        with client_data_lock:
                            client_data[addr]['offer_price'] = offer_price
                        check_trade(addr)
                    elif msg.startswith('SELECT_PARTNER:'):
                        selected_partner_str = msg.split(':', 1)[1]
                        ip, port = selected_partner_str.split(',')
                        selected_partner_addr = (ip, int(port))
                        handle_partner_selection(addr, selected_partner_addr)
                    else:
                        print(f"Unknown message from {addr}: {msg}")
        else:
            client_socket.send('NO_ROLE_PROVIDED'.encode('utf-8'))
            client_socket.close()
            return

    except Exception as e:
        print(f"Error with {addr}: {e}")

    finally:
        client_socket.close()
        with client_data_lock:
            # Remove client from client_data
            if addr in client_data:
                del client_data[addr]
        # Update queue display and broadcast available partners
        update_queue_display(q_signal)
        broadcast_available_partners()
        print(f"Connection closed with {addr}")

def handle_partner_selection(addr, selected_partner_addr):
    with client_data_lock:
        client_info = client_data.get(addr)
        selected_partner_info = client_data.get(selected_partner_addr)
        if not selected_partner_info:
            # Selected partner is not available
            client_info['socket'].send('PARTNER_NOT_AVAILABLE'.encode('utf-8'))
            return

        # Update the client's selected partner
        client_info['selected_partner'] = selected_partner_addr
        # Add this client to the selected partner's 'selected_by' set
        selected_partner_info['selected_by'].add(addr)
        # Check for mutual selection
        if selected_partner_info['selected_partner'] == addr:
            # Mutual selection occurred
            start_trade(addr, selected_partner_addr)
        else:
            # Inform the client that the selection is noted
            client_info['socket'].send('PARTNER_SELECTED'.encode('utf-8'))

def start_trade(addr1, addr2):
    with client_data_lock:
        client1 = client_data[addr1]
        client2 = client_data[addr2]
        # Update states
        client1['state'] = 'trading'
        client2['state'] = 'trading'
        client1['partner_addr'] = addr2
        client2['partner_addr'] = addr1
        client1['offer_price'] = None
        client2['offer_price'] = None
        # Clear selections
        client1['selected_partner'] = None
        client1['selected_by'] = set()
        client2['selected_partner'] = None
        client2['selected_by'] = set()
        # Notify clients to start the trade
        client1['socket'].send('START_TRADE'.encode('utf-8'))
        client2['socket'].send('START_TRADE'.encode('utf-8'))

        # Update pair display
        pair_info = f"Trade started between {addr1} and {addr2}"
        pair_box.signal.emit(pair_info)

def check_trade(addr):
    with client_data_lock:
        client_info = client_data.get(addr)
        if not client_info:
            return
        partner_addr = client_info['partner_addr']
        partner_info = client_data.get(partner_addr)
        if not partner_info:
            return

        # Check if both clients have submitted their offer prices
        if client_info['offer_price'] is not None and partner_info['offer_price'] is not None:
            buyer_info = client_info if client_info['role'] == 'buyer' else partner_info
            seller_info = client_info if client_info['role'] == 'seller' else partner_info

            buyer_price = buyer_info['offer_price']
            seller_price = seller_info['offer_price']

            # Determine if trade is successful
            if buyer_price >= seller_price:
                result = f"Trade Successful! Buyer offered {buyer_price}, Seller asked {seller_price}."
            else:
                result = f"Trade Failed. Buyer offered {buyer_price}, Seller asked {seller_price}."

            # Send result to both clients
            buyer_info['socket'].send(f"TRADE_RESULT:{result}".encode('utf-8'))
            seller_info['socket'].send(f"TRADE_RESULT:{result}".encode('utf-8'))

            # Reset offer prices
            buyer_info['offer_price'] = None
            seller_info['offer_price'] = None

            # Reset states to 'available'
            buyer_info['state'] = 'available'
            seller_info['state'] = 'available'
            buyer_info['partner_addr'] = None
            seller_info['partner_addr'] = None

    # Broadcast updated available partners
    broadcast_available_partners()

def update_queue_display(q_signal):
    queue_string = ""
    with client_data_lock:
        for addr, data in client_data.items():
            queue_string += f"{addr} - {data['role']} - {data['state']}\n"
    q_signal.emit(queue_string)

def broadcast_available_partners():
    with client_data_lock:
        # Prepare lists of available buyers and sellers
        buyers = [addr for addr, data in client_data.items() if data['role'] == 'buyer' and data['state'] == 'available']
        sellers = [addr for addr, data in client_data.items() if data['role'] == 'seller' and data['state'] == 'available']

        for addr, data in client_data.items():
            try:
                if data['state'] == 'available':
                    if data['role'] == 'buyer':
                        partners = sellers
                    else:
                        partners = buyers
                    partner_list_str = ';'.join([f"{p[0]}:{p[1]}" for p in partners])
                    data['socket'].send(f"AVAILABLE_PARTNERS:{partner_list_str}".encode('utf-8'))
            except Exception as e:
                print(f"Error sending available partners to {addr}: {e}")

def server_thread(server_socket, q_signal, p_signal):
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected to {addr}")

        single_client_handler = threading.Thread(target=handle_single_client, args=(client_socket, addr, q_signal))
        single_client_handler.daemon = True
        single_client_handler.start()

def start_match(q_signal, p_signal):
    # Trades are now initiated based on mutual partner selections.
    # Optionally, you can implement manual matching here.
    QMessageBox.information(None, 'Info', 'Trades are now initiated based on mutual partner selections.')

def start_server():
    global pair_box  # Declare pair_box as global so it can be accessed in update_pair_display
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

    # Layout for the window
    layout = QGridLayout(window)

    # Client Dashboard (Queue Dashboard)
    queue_label = QLabel('Client Dashboard', parent=window)
    queue_label.setAlignment(Qt.AlignCenter)
    queue_label.setFont(QFont('Arial', 14))
    layout.addWidget(queue_label, 0, 0)

    queue_box = scrollableBox(window)
    layout.addWidget(queue_box.textEdit, 1, 0)
    queue_box.signal.connect(lambda text: queue_box.textEdit.setText(text))

    # Trade Dashboard
    pair_label = QLabel('Trade Dashboard', parent=window)
    pair_label.setAlignment(Qt.AlignCenter)
    pair_label.setFont(QFont('Arial', 14))
    layout.addWidget(pair_label, 0, 1)

    pair_box = scrollableBox(window)
    layout.addWidget(pair_box.textEdit, 1, 1)
    pair_box.signal.connect(lambda text: pair_box.textEdit.append(text))

    # Start Match Button
    start_match_button = QPushButton("Start Match", window)
    start_match_button.setFont(QFont('Arial', 12))
    start_match_button.clicked.connect(lambda: start_match(queue_box.signal, pair_box.signal))
    layout.addWidget(start_match_button, 2, 0, 1, 2)

    # Parameters
    params = [
        ('Number of Buyers', 'num_buyers', '10'),
        ('Number of Sellers', 'num_sellers', '10'),
        ('Buyer Lower Bound', 'buyer_lower_bound', '5'),
        ('Buyer Upper Bound', 'buyer_upper_bound', '10'),
        ('Seller Lower Bound', 'seller_lower_bound', '0'),
        ('Seller Upper Bound', 'seller_upper_bound', '15'),
        ('Lambda Value', 'lambda_value', '0.1'),
        ('Gamma Value', 'gamma', '0.05'),
        ('d Value', 'dValue', '0'),
        ('p Value', 'pValue', '1'),
        ('Kappa Value', 'kapValue', '1'),
        ('Fixed Cost', 'fixedCost', '0.4'),
        ('Number of Steps', 'num_steps', '10'),
        ('Number of Human Players', 'human_players', '1')
    ]

    # Parameters layout
    params_layout = QGridLayout()
    row = 0
    col = 0
    for index, (label_text, param_name, default_value) in enumerate(params):
        # Parameter label
        label = QLabel(label_text, window)
        label.setFont(QFont('Arial', 10))
        params_layout.addWidget(label, row, col)

        # Parameter input textbox
        text_input = QLineEdit(window)
        text_input.setText(default_value)
        params_layout.addWidget(text_input, row, col + 1)

        # Move to next row
        row += 1

    # Add parameters layout to the main layout
    layout.addLayout(params_layout, 3, 0, 1, 2)

    # Start the server thread
    server_thread_handler = threading.Thread(target=server_thread, args=(server_socket, queue_box.signal, pair_box.signal))
    server_thread_handler.daemon = True
    server_thread_handler.start()

    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_server()
