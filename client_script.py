# client_script.py

import sys
import socket
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont

# Server Configuration
DEFAULT_HOST = 'localhost'  # Default to localhost; will be overridden by user input
DEFAULT_PORT = 12345

class Communicator(QObject):
    start_partner_selection_signal = pyqtSignal()
    available_partners_signal = pyqtSignal(str)
    start_trade_signal = pyqtSignal()
    trade_result_signal = pyqtSignal(str)
    partner_not_available_signal = pyqtSignal()
    partner_selected_signal = pyqtSignal()

class WaitingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Waiting for Trade')
        self.setGeometry(400, 200, 300, 100)
        self.label = QLabel('Waiting', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', 16))
        self.animation_index = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(500)  # Adjust the speed as needed

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def animate(self):
        dots = ['.', '..', '...']
        self.label.setText('Waiting' + dots[self.animation_index % len(dots)])
        self.animation_index += 1

    def stop_animation(self):
        self.animation_timer.stop()

class PartnerSelectionGUI(QWidget):
    def __init__(self, client_socket, role, communicator):
        super().__init__()
        self.client_socket = client_socket
        self.role = role
        self.communicator = communicator
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Select a Partner')
        self.setGeometry(400, 200, 400, 400)

        self.label = QLabel('Available Partners:', self)
        self.label.setFont(QFont('Arial', 12))

        self.partner_list_widget = QListWidget(self)
        self.partner_list_widget.itemClicked.connect(self.select_partner)

        self.info_label = QLabel('', self)
        self.info_label.setFont(QFont('Arial', 10))
        self.info_label.setStyleSheet("color: red")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.partner_list_widget)
        layout.addWidget(self.info_label)
        self.setLayout(layout)

    def update_partner_list(self, partners_str):
        self.partner_list_widget.clear()
        if not partners_str:
            self.info_label.setText('No available partners at the moment.')
            return
        partners = partners_str.split(';')
        for partner in partners:
            ip, port = partner.split(':')
            display_text = f"{ip}:{port}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, (ip, int(port)))
            self.partner_list_widget.addItem(item)
        self.info_label.setText('')

    def select_partner(self, item):
        partner_addr = item.data(Qt.UserRole)
        partner_addr_str = f"{partner_addr[0]},{partner_addr[1]}"
        try:
            self.client_socket.send(f"SELECT_PARTNER:{partner_addr_str}".encode('utf-8'))
            QMessageBox.information(self, 'Partner Selected', f"You have selected {partner_addr[0]}:{partner_addr[1]}")
            self.communicator.partner_selected_signal.emit()
            self.close()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f"Failed to select partner: {e}")

class BuyerGUI(QWidget):
    def __init__(self, client_socket, communicator):
        super().__init__()
        self.client_socket = client_socket
        self.communicator = communicator
        self.init_ui()
        self.start_timer()

    def init_ui(self):
        """Initialize the Buyer GUI."""
        self.setWindowTitle('Buyer Interface')
        self.setGeometry(400, 200, 300, 200)
        self.offer_price_input = QLineEdit(self)
        self.offer_price_input.setPlaceholderText('Enter your offer price')
        self.submit_button = QPushButton('Submit Offer Price', self)
        self.submit_button.clicked.connect(self.submit_offer_price)

        self.timer_label = QLabel('Time left: 10 seconds', self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont('Arial', 10))

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Buyer: Enter your offer price:', self))
        layout.addWidget(self.offer_price_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.timer_label)
        self.setLayout(layout)

    def start_timer(self):
        self.time_left = 10
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_tick)
        self.timer.start(1000)  # 1 second intervals

    def timer_tick(self):
        self.time_left -= 1
        self.timer_label.setText(f'Time left: {self.time_left} seconds')
        if self.time_left <= 0:
            self.timer.stop()
            if not self.offer_price_input.isDisabled():
                # Automatically submit default offer price
                self.offer_price_input.setText('0')  # Default value
                self.submit_offer_price()
                QMessageBox.information(
                    self, 'Time Up', 'Time is up! Offer price submitted automatically.'
                )

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
                self.timer.stop()
            except ValueError:
                QMessageBox.warning(self, 'Input Error', 'Please enter a valid number.')
        else:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid offer price.')

class SellerGUI(QWidget):
    def __init__(self, client_socket, communicator):
        super().__init__()
        self.client_socket = client_socket
        self.communicator = communicator
        self.init_ui()
        self.start_timer()

    def init_ui(self):
        """Initialize the Seller GUI."""
        self.setWindowTitle('Seller Interface')
        self.setGeometry(400, 200, 300, 200)
        self.offer_price_input = QLineEdit(self)
        self.offer_price_input.setPlaceholderText('Enter your offer price')
        self.submit_button = QPushButton('Submit Offer Price', self)
        self.submit_button.clicked.connect(self.submit_offer_price)

        self.timer_label = QLabel('Time left: 10 seconds', self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont('Arial', 10))

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Seller: Enter your offer price:', self))
        layout.addWidget(self.offer_price_input)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.timer_label)
        self.setLayout(layout)

    def start_timer(self):
        self.time_left = 10
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_tick)
        self.timer.start(1000)  # 1 second intervals

    def timer_tick(self):
        self.time_left -= 1
        self.timer_label.setText(f'Time left: {self.time_left} seconds')
        if self.time_left <= 0:
            self.timer.stop()
            if not self.offer_price_input.isDisabled():
                # Automatically submit default offer price
                self.offer_price_input.setText('100')  # Default value
                self.submit_offer_price()
                QMessageBox.information(
                    self, 'Time Up', 'Time is up! Offer price submitted automatically.'
                )

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
                self.timer.stop()
            except ValueError:
                QMessageBox.warning(self, 'Input Error', 'Please enter a valid number.')
        else:
            QMessageBox.warning(self, 'Input Error', 'Please enter a valid offer price.')

class TradeResultDialog(QMessageBox):
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Trade Result')
        self.setText(result)
        self.setStandardButtons(QMessageBox.Ok)

def client_thread(client_socket, role, communicator):
    """Start the client GUI and listener thread."""
    app = QApplication(sys.argv)

    waiting_screen = WaitingScreen()
    waiting_screen.show()

    # Variables to hold GUI references
    gui = {'main_gui': None, 'partner_gui': None}

    # Define slots to be called when signals are emitted
    def start_partner_selection():
        waiting_screen.stop_animation()
        waiting_screen.close()
        gui['partner_gui'] = PartnerSelectionGUI(client_socket, role, communicator)
        gui['partner_gui'].show()

    def update_available_partners(partners_str):
        if gui['partner_gui']:
            gui['partner_gui'].update_partner_list(partners_str)

    def start_trade():
        if gui['partner_gui']:
            gui['partner_gui'].close()
        if role == 'buyer':
            gui['main_gui'] = BuyerGUI(client_socket, communicator)
        else:
            gui['main_gui'] = SellerGUI(client_socket, communicator)
        gui['main_gui'].show()

    def display_trade_result(result):
        if gui['main_gui']:
            QMessageBox.information(gui['main_gui'], 'Trade Result', result)
            # Reset GUI for another trade
            gui['main_gui'].offer_price_input.setDisabled(False)
            gui['main_gui'].submit_button.setDisabled(False)
            gui['main_gui'].offer_price_input.clear()
            gui['main_gui'].start_timer()
            # After trade, go back to partner selection
            gui['main_gui'].close()
            gui['main_gui'] = None
            communicator.start_partner_selection_signal.emit()

    def handle_partner_not_available():
        QMessageBox.warning(None, 'Partner Not Available', 'The selected partner is not available.')

    def handle_partner_selected():
        QMessageBox.information(None, 'Partner Selected', 'Partner selection sent successfully.')

    # Connect signals to slots
    communicator.start_partner_selection_signal.connect(start_partner_selection)
    communicator.available_partners_signal.connect(update_available_partners)
    communicator.start_trade_signal.connect(start_trade)
    communicator.trade_result_signal.connect(display_trade_result)
    communicator.partner_not_available_signal.connect(handle_partner_not_available)
    communicator.partner_selected_signal.connect(handle_partner_selected)

    # Start a thread to listen for messages from the server
    listener_thread = threading.Thread(
        target=listen_to_server, args=(client_socket, communicator)
    )
    listener_thread.daemon = True
    listener_thread.start()

    sys.exit(app.exec_())

def listen_to_server(client_socket, communicator):
    """Listen for messages from the server and handle them."""
    while True:
        try:
            message = client_socket.recv(4096).decode('utf-8')
            if not message:
                print("Server closed the connection.")
                break
            # Handle multiple messages concatenated together
            messages = message.strip().split('\n')
            for msg in messages:
                if msg == '':
                    continue
                if msg == 'START_TRADE':
                    communicator.start_trade_signal.emit()
                elif msg.startswith('AVAILABLE_PARTNERS:'):
                    partners_str = msg.split(':', 1)[1]
                    communicator.available_partners_signal.emit(partners_str)
                elif msg.startswith('TRADE_RESULT:'):
                    result = msg.split(':', 1)[1]
                    communicator.trade_result_signal.emit(result)
                elif msg == 'PARTNER_NOT_AVAILABLE':
                    communicator.partner_not_available_signal.emit()
                elif msg == 'PARTNER_SELECTED':
                    communicator.partner_selected_signal.emit()
                elif msg == 'START_GAME':
                    # Initial signal to start partner selection
                    communicator.start_partner_selection_signal.emit()
                else:
                    print(f"Unknown message from server: {msg}")
        except Exception as e:
            print(f"Connection closed or error occurred: {e}")
            break

def main():
    """Main function to start the client."""
    # Prompt user for server IP and port
    server_ip = input(f"Enter server IP address (default: {DEFAULT_HOST}): ").strip()
    if server_ip == '':
        server_ip = DEFAULT_HOST

    server_port_input = input(f"Enter server port (default: {DEFAULT_PORT}): ").strip()
    if server_port_input == '':
        server_port = DEFAULT_PORT
    else:
        try:
            server_port = int(server_port_input)
        except ValueError:
            print("Invalid port number. Using default port.")
            server_port = DEFAULT_PORT

    role = input("Enter your role (buyer/seller): ").strip().lower()
    if role not in ['buyer', 'seller']:
        print("Invalid role. Please enter 'buyer' or 'seller'.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        return

    # Send the role to the server
    client_socket.send(f"ROLE:{role}".encode('utf-8'))

    communicator = Communicator()
    client_thread(client_socket, role, communicator)

if __name__ == '__main__':
    main()
