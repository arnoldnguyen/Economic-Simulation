# client_script.py

import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox

HOST = 'localhost'
PORT = 12345

class BuyerGUI(QWidget):
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.init_ui()

    def init_ui(self):
        """Initialize the Buyer GUI."""
        self.setWindowTitle('Buyer Interface')
        self.offer_price_input = QLineEdit(self)
        self.submit_button = QPushButton('Submit Offer Price', self)
        self.submit_button.clicked.connect(self.submit_offer_price)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Enter your offer price:', self))
        layout.addWidget(self.offer_price_input)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def submit_offer_price(self):
        """Send the buyer's offer price to the server."""
        offer_price = self.offer_price_input.text()
        if offer_price:
            try:
                float(offer_price)  # Validate input
                message = f"OFFER_PRICE:{offer_price}"
                self.client_socket.send(message.encode('utf-8'))
                self.offer_price_input.setDisabled(True)
                self.submit_button.setDisabled(True)
            except ValueError:
                QMessageBox.warning(self, 'Input Error', 'Please enter a valid number.')
        else:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid offer price.')

class SellerGUI(QWidget):
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.init_ui()

    def init_ui(self):
        """Initialize the Seller GUI."""
        self.setWindowTitle('Seller Interface')
        self.offer_price_input = QLineEdit(self)
        self.submit_button = QPushButton('Submit Offer Price', self)
        self.submit_button.clicked.connect(self.submit_offer_price)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Enter your offer price:', self))
        layout.addWidget(self.offer_price_input)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def submit_offer_price(self):
        """Send the seller's offer price to the server."""
        offer_price = self.offer_price_input.text()
        if offer_price:
            try:
                float(offer_price)  # Validate input
                message = f"OFFER_PRICE:{offer_price}"
                self.client_socket.send(message.encode('utf-8'))
                self.offer_price_input.setDisabled(True)
                self.submit_button.setDisabled(True)
            except ValueError:
                QMessageBox.warning(self, 'Input Error', 'Please enter a valid number.')
        else:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid offer price.')

def client_thread(client_socket, role):
    """Start the client GUI and listener thread."""
    app = QApplication(sys.argv)
    if role == 'buyer':
        gui = BuyerGUI(client_socket)
    else:
        gui = SellerGUI(client_socket)
    gui.show()

    # Start a thread to listen for messages from the server
    listener_thread = threading.Thread(target=listen_to_server, args=(client_socket, gui))
    listener_thread.daemon = True
    listener_thread.start()

    sys.exit(app.exec_())

def listen_to_server(client_socket, gui):
    """Listen for messages from the server and handle them."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith('TRADE_RESULT:'):
                result = message.split(':', 1)[1]
                QMessageBox.information(gui, 'Trade Result', result)
                # Reset GUI for another trade
                gui.offer_price_input.setDisabled(False)
                gui.submit_button.setDisabled(False)
                gui.offer_price_input.clear()
            elif message.startswith('PAIRED_WITH_'):
                pass  # You can handle pairing notifications here
            else:
                print(f"Unknown message from server: {message}")
        except Exception as e:
            print(f"Connection closed: {e}")
            break

def main():
    """Main function to start the client."""
    role = input("Enter your role (buyer/seller): ").strip().lower()
    if role not in ['buyer', 'seller']:
        print("Invalid role. Please enter 'buyer' or 'seller'.")
        return
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    # Send the role to the server
    client_socket.send(f"ROLE:{role}".encode('utf-8'))

    client_thread(client_socket, role)

if __name__ == '__main__':
    main()
