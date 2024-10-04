import socket
import sys
import threading
import queue

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy

from global_functions import *
from basic_utils import textBox, scrollableBox

# ONLY SERVER THREAD ADDS CLIENTS TO QUEU AND ASSIGNS PAIRS. SO NO NEED FOR LOCKS
# _________________________________________________________________________________________________________________________
# PAIRING QUEUE
client_queue = queue.Queue()
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

        signal_string = f"{addr[0]},\t{addr[1]}"

        single_client_handler = threading.Thread(target=handle_single_client, args=(client_socket, addr))
        single_client_handler.start()

        # If two clients are in the queue, pair them together
        if client_queue.qsize() >= 2:
            print("paired")
            client1, addr1 = client_queue.get()
            client2, addr2 = client_queue.get()
            
            pair_map[addr1] = addr2
            pair_map[addr2] = addr1

            signal_string = ""
            p_signal.emit(f"{addr1[0]}, {addr1[1]} is connected to {addr2[0]}, {addr2[1]}")

        q_signal.emit(signal_string)



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

    queue_box = scrollableBox(window)
    ui_grid(queue_box.textEdit, pos=(1, 4), size=(1, 9), margin=(10, 10))
    queue_box.signal.connect(lambda text: queue_box.textEdit.append(text) if text != "" else queue_box.textEdit.clear())


    pair_box = scrollableBox(window)
    ui_grid(pair_box.textEdit, pos=(2, 4), size=(3, 9), margin=(10, 10))
    pair_box.signal.connect(lambda text: pair_box.textEdit.append(text))



    server_thread_handler = threading.Thread(target=server_thread, args=(server_socket, queue_box.signal, pair_box.signal))
    server_thread_handler.start()



    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_server()
