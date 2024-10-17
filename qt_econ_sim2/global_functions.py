from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QGridLayout, QSizePolicy, QTextEdit
from PyQt5.QtGui import QFont

from global_functions import *

NUM_ROWS = 15
NUM_COLS = 5

WIDTH = 750
HEIGHT = 750

PORT = 9986
SERVER_HOST = '127.0.0.1'
CLIENT_HOST = "127.0.0.1"

# THIS CODE, WHICH RUNS ON THE SERVER SIDE, OUTPUTS THE SERVER HOST NAME WHICH THE CLIENT CONENCTS TO IN CLIENT_HOST
# print(socket.gethostbyname(socket.gethostname()))


def ui_grid(ui_element, pos, size = None, margin = None, area = (None), font_size = 12, allign = "l"):
    font = QFont("Arial", font_size)
    ui_element.setFont(font)
    ui_element.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    ui_element.setStyleSheet("padding: 0px; margin: 0px;")
    ui_element.setContentsMargins(0, 0, 0, 0)

    dx = WIDTH // NUM_COLS
    dy = HEIGHT // NUM_ROWS

    px_pos = ((pos[0] * dx), (pos[1] * dy))

    if size == None:
        px_size_x = dx
        px_size_y = dy
    else:
        px_size_x = (size[0] - pos[0] + 1) * dx
        px_size_y = (size[1] - pos[1] + 1) * dy

    px_size = (px_size_x, px_size_y)

    if margin != None and area != None:
        sys.exit("ui_grid either accepts margin or area, not both")

    if margin != None:
        px_size = (px_size_x - margin[0], px_size_y - margin[1])
    
    if area != None:
        if area[0] > dx:
            print(f"Warning: area[0] > dx. area[0] = {area[0]}, dx = {dx}")

        if area[1] > dy:
            print(f"Warning: area[1] > dy. area[1] = {area[1]}, dy = {dy}")

        px_size = (area[0], area[1])

    if allign == "r":
        px_pos = (px_pos[0] + dx - px_size[0],  px_pos[1] + dy - px_size[1])


    ui_element.setFixedSize(px_size[0], px_size[1])  # Width: 200, Height: 30

    ui_element.move(px_pos[0], px_pos[1])
