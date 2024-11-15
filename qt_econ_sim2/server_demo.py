import socket
import sys
import threading
import queue

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy, QListWidget
from PyQt5.QtCore import pyqtSignal, Qt, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont

from global_functions import *
from basic_utils import textBox, scrollableBox, pushButton, timeSystem

import random as rand

hostname = socket.gethostname()  # Get the server's hostname
server_ip = socket.gethostbyname(hostname)  # Get the IP address based on the hostname

print(f"Server IP Address: {server_ip}")

# _________________________________________________________________________________________________________________________
# PAIRING QUEUE
client_queue = queue.Queue()
queue_lock = threading.Lock()

# HAHSMAP: CLIENT ADDRESS -> IF IT IS PAIRED, PARTNER ADDRESS ELSE NONE
#pair_map = {}
# _________________________________________________________________________________________________________________________

# HAHSMAP: CLIENT ID -> CLIENT AGENT (DO AGENT.SOCKET TO SEND)
client_map = {}

# PUBLIC RESOURCE, NEED TO LOCK TO AVOID RACE CONDITIONS
client_map_lock = threading.Lock()

# NO OTHER THREAD SHOULD TOUCH THIS VARIABLE OTHER THAN HANDLE SINGLE CLIENT
unique_id_generator = 1
id_gen_lock = threading.Lock()

def handle_time_up():
    print(f"Notify All Parties Time Is Up")
    for k, v in client_map.items():
        print(f"Notify {v.unique_id} about time end")
        v.socket.send(f"TIME UP;".encode('utf-8'))
        for mssg in v.batch:
            v.socket.send(mssg.encode('utf-8'))
        

def find_agent(target_addr):
    for unique_id in client_map:
        with client_map_lock:
            if client_map[unique_id].addr == target_addr:
                return client_map[unique_id]

class Agent():
    def __init__(self, unique_id, socket, partner_addr, self_addr):
        self.unique_id = unique_id
        self.socket = socket
        self.partners = []
        self.partner_id = partner_addr
        self.pursued = None
        self.addr = self_addr
        self.batch = []

def handle_single_client(client_socket, addr, handle_single_client_args):
    global unique_id_generator
    curr_agent = None
    
    queue_box = handle_single_client_args[0]
    
    with client_map_lock:
        # THE TRANSITION TO AGENTS IS INCOMPLETE. ALSO DO IT FOR THE QUEUE
        with id_gen_lock:
            print(f"ADDED id: {unique_id_generator} with addr: {addr} to client map")
            client_map[unique_id_generator] = Agent(unique_id_generator, client_socket, partner_addr=None, self_addr=addr)  # Add the client to the dictionary
            curr_agent = client_map[unique_id_generator]
            unique_id_generator += 1

    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(f"Server Recieved The Following: {message}")

                if message[:len("SERVER:")] == "SERVER:":
                    message = message[len("SERVER:"):]

                    if message[:len("CHANGE PARTNER:")] == "CHANGE PARTNER:":
                        switch_to_id = int(message.split(":")[1])
                        target_agent = client_map[switch_to_id]
                        target_agent.socket.send(f"SWITCH PARTNER:{curr_agent.unique_id};".encode('utf-8'))
                        curr_agent.pursued = switch_to_id
                        
                        print(f"LOOK HERE CURR ID: {curr_agent.unique_id} CURR PURUED: {curr_agent.pursued}")
                        print(f"SENT: (SWITCH PARTNER:{curr_agent.unique_id};) TO {target_agent.unique_id}")
                  
                    elif message[:len("Y:")] == "Y:":
                        switch_to_id = int(message.split(":")[1])
                        target_agent = client_map[switch_to_id]

                        print(f"In Y: checking if T pursued: {target_agent.pursued} == Curr id: {curr_agent.unique_id}")

                        if target_agent.pursued == curr_agent.unique_id:
                            target_agent.pursued = None
                            print(1)

                            print(f"T Partner: {target_agent.partner_id}")
                            old_target_agent = client_map[target_agent.partner_id]

                            print(f"C Partner: {target_agent.partner_id}")
                            old_curr_agent = client_map[curr_agent.partner_id]
                            print("a")

                            old_target_agent.partner_id = None
                            old_target_agent.socket.send(f"PARTNER LEFT;".encode('utf-8'))
                            print("b")

                            old_curr_agent.partner_id = None
                            old_curr_agent.socket.send(f"PARTNER LEFT;".encode('utf-8'))
                            print(4)

                            QMetaObject.invokeMethod(
                                queue_box.textEdit, 
                                "append", 
                                Qt.QueuedConnection, 
                                Q_ARG(str, f"{old_target_agent.addr}")
                            )

                            QMetaObject.invokeMethod(
                                queue_box.textEdit, 
                                "append", 
                                Qt.QueuedConnection, 
                                Q_ARG(str, f"{old_curr_agent.addr}")
                            )

                            target_agent.partner_id = curr_agent.unique_id
                            curr_agent.partner_id = target_agent.unique_id
                            print(5)

                            print(target_agent.socket)
                            target_agent.socket.send(f"You are now paired with {curr_agent.unique_id};".encode('utf-8'))
                            print(6)

                            curr_agent.socket.send(f"You are now paired with {target_agent.unique_id};".encode('utf-8'))
                            print(7)

                            print(f"THEY HAVE BEEN PAIRED UP")

                elif message[:len("PROPOSE TRADE:")] == "PROPOSE TRADE:":
                    print("handle PROPOSE TRADE")
                    #print(f"trade id becomes = |{message.split(":")[1].split(";")[0]}|")
                    if curr_agent.pursued != -1:
                        print("you cannot approach more than one person")
                    
                    trade_id = int(message.split(":")[1])
                    print(f"target {trade_id}")
                    curr_agent.pursued = trade_id
                    #client_map[trade_id].socket.send(f"INIT REQUEST:{curr_agent.unique_id},{offer_price};".encode('utf-8'))
                    client_map[trade_id].batch.append(f"INIT REQUEST:{curr_agent.unique_id};")
                    #client_map[trade_id].socket.send(f"{curr_agent.unique_id} would like to trade with you! Their offer price is ${offer_price}".encode('utf-8'))

                elif message[:len("ACCEPT REQUEST FROM:")] == "ACCEPT REQUEST FROM:":
                    print("handle client accepting")
                    print(f"SPLIT: {message.split(':')[1]}")
                    trade_id = int(message.split(":")[1])
                    print(f"Pursued: {client_map[trade_id].pursued}, Curr ID: {curr_agent.unique_id}")
                    if client_map[trade_id].pursued == curr_agent.unique_id:
                        print(f"IDS match, time to pair")
                        client_map[trade_id].partner_id = curr_agent.unique_id
                        curr_agent.partner_id = client_map[trade_id].unique_id
                        
                        curr_agent.socket.send(f"PARTNER ID SET:{trade_id};".encode('utf-8'))
                        client_map[trade_id].socket.send(f"PARTNER ID SET:{curr_agent.unique_id};".encode('utf-8'))


                elif message[:len("MSSG:")] == "MSSG:":
                    print("handle message broadcast")
                    details = message.split(":")[1]
                    trade_id = int(details.split(";")[0])
                    mssg = details.split(";")[1]
                    print(f"details {message}, t_id: {trade_id}, mssg:{mssg}")
                    client_map[trade_id].socket.send(f"MSSG:{curr_agent.unique_id},{mssg};".encode('utf-8'))

                    # PRINT AT SERVER END
                else:
                    print(f"Message from {addr} to Server: \n\"{message}\"")

            else:
                print(f"{addr} disconnected.")
                break

    except Exception as e:
        print(f"Error with {addr}: {e}")
    
    finally:
        client_socket.close()

        # MAYBE NEED TO DEL THE CLIENT PAIR_MAP AND CLIENT_QUEUE INDEXES TOO ???
        del client_map[curr_agent.unique_id]  # Remove client from dictionary
        
        print(f"Connection closed with {addr}")

def server_thread(server_socket, q_signal, handle_single_client_args):
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected to {client_socket} from {addr}")
        
        client_queue.put((client_socket, addr))

        print(f"\n\nPASSING Addr: {addr} to HSC\n\n")

        single_client_handler = threading.Thread(target=handle_single_client, args=(client_socket, addr, handle_single_client_args))
        single_client_handler.start()
        
        queue_list = list(client_queue.queue)
        queue_string = ""
             
        for i in queue_list:
            client, addr = i
            queue_string += f"{addr}\n"
        
        q_signal.emit(queue_string)

def create_adj_list(q_dup, pair_box, time_system):
    # CREATE PROBABILITIES
    n = len(q_dup)

    n_comb = (n * (n-1)) / 2
    num_pairs = rand.randint(n, n_comb)

    print(f"n: {n}")

    for i in range(num_pairs):
        ind_1 = rand.randint(1, n-1)
        ind_2 = rand.randint(1, n-1)

        print(f"ind 1: {ind_1}, ind_2: {ind_2}")

        agent_1 = find_agent(q_dup[ind_1][1])
        agent_2 = find_agent(q_dup[ind_2][1])

        if agent_1.unique_id != agent_2.unique_id and agent_1.unique_id not in agent_2.partners and agent_2.unique_id not in agent_1.partners:
            agent_1.partners.append(agent_2.unique_id)
            agent_2.partners.append(agent_1.unique_id)


    for k, v in client_map.items():
        print(f"UNIQUE ID: {v.unique_id} PARTNERS: {v.partners}")        

        player_list_str = "\n".join(map(str, v.partners))
        
        v.socket.send(f"Player List:{player_list_str};".encode('utf-8'))

    time_system.timer.start()
    time_system.label.setVisible(True)

def start_match(q_signal, pair_box, time_system):

    print()
    print("yer")
    print()

    q_dup = list(client_queue.queue)

    pair_box.clear()
    for i in q_dup:
        pair_box.addItem(f"{find_agent(i[1]).unique_id}")


    create_adj_list(q_dup, pair_box, time_system)

    while not client_queue.empty():
        client_queue.get()

    with queue_lock:
        # HERE THE PAIR MAP CODE IS MIXED WITH THE CLIENT MAP CODE. TRY TO FIX IT
        # If two clients are in the queue, pair them together
        '''
        while client_queue.qsize() >= 2:
            client1, addr1 = client_queue.get()
            client2, addr2 = client_queue.get()

            agent1 = find_agent(addr1)
            agent2 = find_agent(addr2)

            agent1.partner_id = agent2.unique_id
            agent2.partner_id = agent1.unique_id

            #print(f"MAP: {client_map}")

            client1.send("You Are Connected To The Server;".encode('utf-8'))
            client1.send(f"Partner ID: {find_agent(addr2).unique_id};".encode('utf-8'))
            
            client2.send("You Are Connected To The Server;".encode('utf-8'))
            client2.send(f"Partner ID: {find_agent(addr1).unique_id};".encode('utf-8'))

            p_signal.emit(f"{addr1[0]}, {addr1[1]} is connected to {addr2[0]}, {addr2[1]}")
        '''

        queue_list = list(client_queue.queue)
        queue_string = ""
                
        for i in queue_list:
            client, addr = i
            queue_string += f"{addr}\n"
        
        q_signal.emit(queue_string)

    print("CLIENT MAP")

    player_list_str = ""

    for unique_id in client_map:
        player_list_str += f"{str(unique_id)}\n"

    for unique_id in client_map:
        socket = client_map[unique_id].socket
        
        # OLD PLAYER LIST
        #socket.send(f"Player List:{player_list_str};".encode('utf-8'))
        
        #print(f"Key: {addr}, Val: {val}")    

def start_server():
    
    app = QApplication(sys.argv)
    # BUILD THE WINDOW
    window = QWidget()
    window.setWindowTitle('Hello, PyQt!')
    window.setGeometry(100, 100, WIDTH, HEIGHT)

    time_system = timeSystem(window, 30)
    time_system.time_up.connect(handle_time_up)
    ui_grid(time_system.label, pos=(0, 5))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Set socket options to reuse the address
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((SERVER_HOST, PORT))
    
    server_socket.listen(5)
    print(f"Server listening on {SERVER_HOST}:{PORT}")

    print(f"Socket Hostname: {socket.gethostbyname(socket.gethostname())}")

    queue_label = QLabel('Queue Dashboard', parent=window)
    queue_label.setAlignment(Qt.AlignCenter)
    ui_grid(queue_label, pos=(1, 3))

    queue_box = scrollableBox(window)
    ui_grid(queue_box.textEdit, pos=(1, 4), size=(1, 9), margin=(10, 10))
    queue_box.signal.connect(lambda text: queue_box.textEdit.setText(text))

    pair_label = QLabel('Pair Dashboard', parent=window)
    pair_label.setAlignment(Qt.AlignCenter)
    ui_grid(pair_label, pos=(2, 3), size=(3, 3))

    pair_box = QListWidget(window)
    ui_grid(pair_box, pos=(2, 4), size=(2, 9), margin=(10, 10))
    #pair_box.signal.connect(lambda text: pair_box.textEdit.append(text))
    
    pair_box_2 = scrollableBox(window)
    ui_grid(pair_box_2.textEdit, pos=(3, 4), size=(3,9), margin=(10, 10))

    pair_box.itemClicked.connect(lambda item: pair_box_2.textEdit.setText("\n".join(map(str, client_map[int(item.text())].partners))))

    start_match_button = pushButton("Start Match", window)
    ui_grid(start_match_button.button, pos=(0, 4), margin=(10, 10))
    start_match_button.button.clicked.connect(lambda: start_match(queue_box.signal, pair_box, time_system))

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

    handle_single_client_args = [queue_box]


    server_thread_handler = threading.Thread(target=server_thread, args=(server_socket, queue_box.signal, handle_single_client_args))
    server_thread_handler.start()

    print(f"LOOK HEREEEE: {socket.gethostbyname(socket.gethostname())}")


    window.show()
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    start_server()
