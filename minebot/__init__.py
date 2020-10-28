#!/usr/bin/env python
"""GUI for Mine Sweeper.
Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from __future__ import print_function
import argparse
import time
import threading

try:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QCore import QWidget, QApplication, QGridLayout
except ImportError:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout

from minesweeper import MSGame, gui

def test_action(game: MSGame, grid_wg: gui.GameWidget):
    import time
    for i in range(10):
        print('click:', i)
        game.play_move('click', i, i)
        grid_wg.update_grid()
        time.sleep(0.5)

def ms_game_main(board_width, board_height, num_mines, port, ip_add):
    """Main function for Mine Sweeper Game.
    Parameters
    ----------
    board_width : int
        the width of the board (> 0)
    board_height : int
        the height of the board (> 0)
    num_mines : int
        the number of mines, cannot be larger than
        (board_width x board_height)
    port : int
        UDP port number, default is 5678
    ip_add : string
        the ip address for receiving the command,
        default is localhost.
    """
    ms_game = MSGame(board_width, board_height, num_mines,
                     port=port, ip_add=ip_add)

    ms_app = QApplication([])

    ms_window = QWidget()
    ms_window.setAutoFillBackground(True)
    ms_window.setWindowTitle("Mine Sweeper")
    ms_layout = QGridLayout()
    ms_window.setLayout(ms_layout)

    fun_wg = gui.ControlWidget()
    grid_wg = gui.GameWidget(ms_game, fun_wg)


    def reset_button_state():
        """Reset button state."""
        grid_wg.reset_game()

    fun_wg.reset_button.clicked.connect(reset_button_state)

    ms_layout.addWidget(fun_wg, 0, 0)
    ms_layout.addWidget(grid_wg, 1, 0)
    ms_window.show()
    threading.Thread(target=test_action, args=(ms_game, grid_wg)).start()

    ms_app.exec_()
    # test_action(ms_game, grid_wg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mine Sweeper Minesweeper \
                                                  with interfaces for \
                                                  Reinforcement Learning \
                                                  by Yuhuang Hu")
    parser.add_argument("--board-width", type=int,
                        default=20,
                        help="width of the board.")
    parser.add_argument("--board-height", type=int,
                        default=20,
                        help="height of the board.")
    parser.add_argument("--num-mines", type=int,
                        default=40,
                        help="number of mines.")
    parser.add_argument("--port", type=int,
                        default=5678,
                        help="The port for TCP connection.")
    parser.add_argument("--ip-add", type=str,
                        default="127.0.0.1",
                        help="The IP address for TCP connection.")
    args = parser.parse_args()
    ms_game_main(**vars(args))
    