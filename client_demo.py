# client_demo.py

import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, Qt

HOST = 'localhost'
PORT = 12345

class ClientWorker(QObject):
    # Define a signal to update the GUI with trade results
    trade_result_signal = pyqtSignal(str)
    paired_signal = pyqtSignal(str)

    def __init__(self, client_socket, role):
        super().__init__()
        self.client_socket = client_socket
        self.role = role

    def run(self):
        # Send the role to the server
        self.client_socket.send(f"ROLE:{self.role}".encode('utf-8'))

        # Listen for messages from the server
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break  # Connection closed

                if message.startswith('TRADE_RESULT:'):
                    result = message.split(':', 1)[1]
                    # Emit a signal with the trade result
                    self.trade_result_signal.emit(result)
                elif message.startswith('PAIRED_WITH_'):
                    # Handle pairing notification
                    self.paired_signal.emit(message)
                else:
                    print(f"Unknown message from server: {message}")
            except Exception as e:
                print(f"Connection closed: {e}")
                break

        self.client_socket.close()

class BuyerGUI(QWidget):
    def __init__(self, client_socket, worker):
        super().__init__()
        self.client_socket = client_socket
        self.worker = worker
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

    def display_trade_result(self, result):
        """Display the trade result to the user."""
        QMessageBox.information(self, 'Trade Result', result)
        # Reset GUI for another trade
        self.offer_price_input.setDisabled(False)
        self.submit_button.setDisabled(False)
        self.offer_price_input.clear()

class SellerGUI(QWidget):
    def __init__(self, client_socket, worker):
        super().__init__()
        self.client_socket = client_socket
        self.worker = worker
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

    def display_trade_result(self, result):
        """Display the trade result to the user."""
        QMessageBox.information(self, 'Trade Result', result)
        # Reset GUI for another trade
        self.offer_price_input.setDisabled(False)
        self.submit_button.setDisabled(False)
        self.offer_price_input.clear()

def main():
    """Main function to start the client."""
    role = input("Enter your role (buyer/seller): ").strip().lower()
    if role not in ['buyer', 'seller']:
        print("Invalid role. Please enter 'buyer' or 'seller'.")
        return

    # Create the client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    # Create a worker object to handle communication with the server
    worker = ClientWorker(client_socket, role)

    # Start the GUI application
    app = QApplication(sys.argv)

    if role == 'buyer':
        gui = BuyerGUI(client_socket, worker)
    else:
        gui = SellerGUI(client_socket, worker)

    # Connect the worker's signals to the GUI methods
    worker.trade_result_signal.connect(gui.display_trade_result)
    # You can handle the paired_signal if needed

    # Start the worker in a separate thread
    worker_thread = threading.Thread(target=worker.run)
    worker_thread.daemon = True
    worker_thread.start()

    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
