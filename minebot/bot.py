from __future__ import print_function
import argparse
import time
from minesweeper.msboard import MSBoard
import random
from itertools import combinations

try:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QCore import QWidget, QApplication, QGridLayout
except ImportError:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout

from minesweeper import MSGame, gui
from threading import Thread
import numpy as np
from typing import Iterator, List
from cached_property import cached_property
import pyautogui

class Cliker:

    def __init__(self, nwidth=9, nheight=9, left=663, top=366, width=239, height=230):
        self.nwidth = nwidth
        self.nheight = nheight
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.button_pos = {
            'left': 766,
            'top': 301,
            'width': 39,
            'height': 37,
        }
        self.timer_pos = {
            'left': 1038,
            'top': 426,
        }
        self.start_time = -1
        self.ceil_centers = self.cal_centers()

    def start_game(self):
        x = self.button_pos['left'] + random.randint(10, self.button_pos['width']-9)
        y = self.button_pos['top'] + random.randint(10, self.button_pos['height']-9)
        pyautogui.moveTo(x, y)
        pyautogui.click(x, y)

    def start_timer(self):
        self.start_time = time.time()
        x = self.timer_pos['left'] + random.randint(9, 30)
        y = self.timer_pos['top'] + random.randint(9, 25)
        pyautogui.moveTo(x, y)
        pyautogui.click(x, y)
        # pyautogui.click(x, y)
        
    def end_timer(self):
        x = self.timer_pos['left'] + random.randint(9, 30)
        y = self.timer_pos['top'] + random.randint(9, 25)
        pyautogui.moveTo(x, y)
        print('timer end.............')
        print(time.time() - self.start_time)


    def cal_centers(self):
        cells = {}
        cw = self.width / self.nwidth
        rh = self.height / self.nheight
        for r in range(self.nheight):
            for c in range(self.nwidth):
                cells[(c, r)] = (int(self.left + c*cw + 0.5*cw), int(self.top + r*rh + 0.5*rh))
        return cells

    def click(self, action, x, y):
        pos = self.ceil_centers[(x, y)]
        pyautogui.moveTo(*pos)
        if action == 'click':
            pyautogui.click(*pos)
        elif action == 'flag':
            pyautogui.rightClick(*pos)
        else:
            raise ValueError(action)


class Rule:

    def __init__(self, ceil: 'Ceil'):
        self.ceil = ceil

    @property
    def around_blank_ceils(self)->set:
        return set(self.ceil.around_blank_ceils)

    @property
    def sm(self):
        self.ceil.status - self.ceil.n_mine

    def is_arounds_mines(self):
        return self.sm == len(self.arounds)

    def is_arounds_nums(self):
        return self.sm == 0 and len(self.arounds)>0

class Ceil:

    def __init__(self, x:int, y:int, board: MSBoard):
        self.x = x
        self.y = y
        self.position = (x, y)
        self.board = board

    def __eq__(self, other):
        return self.position==other.position

    def __hash__(self):
        return hash(self.position)

    def __str__(self):
        return '({}, {}, {})'.format(self.x, self.y, self.status)

    def __repr__(self):
        return '({}, {}, {})'.format(self.x, self.y, self.status)

    @property
    def xmax(self)->int:
        return self.board.board_width-1

    @property
    def ymax(self)->int:
        return self.board.board_height-1

    @property
    def status(self):
        '''
            0-8 is number of mines in srrounding.
            9 is flagged field.
            10 is questioned field.
            11 is undiscovered field.
            12 is a mine field.
        '''
        return self.board.info_map[self.y, self.x]


    @property
    def starterx(self)->int:
        x = self.x-1
        if x <0:
            x = 0
        return x
    
    @property
    def startery(self)->int:
        y = self.y-1
        if y <0:
            y = 0
        return y

    @property
    def enderx(self)->int:
        x = self.x + 1
        if x > self.xmax:
            x = self.xmax
        return x
    
    @property
    def endery(self)->int:
        y = self.y + 1
        if y > self.ymax:
            y = self.ymax
        return y
    
    

    @property
    def around_board(self)->np.array:
        # print('borders:', self.startery, self.endery, self.starterx, self.enderx, self.position)
        return self.board.info_map[self.startery:self.endery+1, self.starterx:self.enderx+1]

    @property
    def around_ceils(self)->List['Ceil']:
        ceils = []
        for x in range(self.x-1, self.x+2):
            if x<0 or x>self.xmax:
                continue
            for y in range(self.y-1, self.y+2):
                if y<0 or y>self.ymax or (x==self.x and y==self.y):
                    continue
                ceils.append(Ceil(x, y, self.board))
        return ceils

    @property
    def around_blank_ceils(self)->List['Ceil']:
        cs = []
        for c in self.around_ceils:
            if c.is_blank:
                cs.append(c)
        return cs

    @property
    def n_num(self):
        n = (self.around_board<9).sum()
        if self.is_num:
            n -= 1
        return n

    @property
    def n_blank(self):
        # print(self.around_board)
        n = (self.around_board==11).sum()
        if self.is_blank:
            n -= 1
        # print('n blank:', n, self.position)
        return n
    
    @property
    def n_mine(self):
        n = (self.around_board==9).sum()
        n += (self.around_board==12).sum()
        if self.is_mine:
            n -= 1
        # print('N mine:', n)
        return n

    @property
    def is_num(self):
        return self.status<9

    @property
    def is_mine(self):
        return self.status==9 or self.status==12

    @property
    def is_blank(self):
        return self.status==11
        
    @property
    def around_mine_pro(self)->float:
        '''周围空ceil是雷的概率'''
        assert self.is_num
        if self.n_blank>0:
            return (self.status-self.n_mine)/self.n_blank
        else:
            return -1.0

    @property
    def around_num_ceils(self)->list:
        ceils = []
        for ac in self.around_ceils:
            if ac.is_num:
                ceils.append(ac)
        return ceils

    @property
    def sure_ceils(self):
        '''可以确定的ceils'''
        assert self.is_num
        if self.around_mine_pro == 1:
            # 全都是雷
            return 1, self.around_blank_ceils
        elif self.around_mine_pro == 0:
            # 没有雷
            return 0, self.around_blank_ceils
        return -1, None
    
    @property
    def is_useless_num(self):
        if self.is_num:
            for c in self.around_ceils:
                if c.is_blank:
                    return False
            return True
        return False

    @property
    def varname(self)->str:
        return 'x{}_{}'.format(self.x, self.y)

    @property
    def n_left_mines(self)->int:
        # print('n_left_mines:', self.status - self.n_mine, self.position)
        return self.status - self.n_mine

    @property
    def is_arounded_mines(self):
        return self.n_left_mines == self.n_blank

    @property
    def is_arounded_nums(self):
        return self.n_left_mines == 0


class Brain:

    def __init__(self, game: MSGame):
        self.game = game
        self.cleare_pos = []
        self.ceils = {} # positon -> Ceil
        self.pros = np.zeros((self.board.board_height, self.board.board_width))
        self.useless_ceils = [] # 周围没有blank的ceil

    @property
    def board(self):
        return self.game.board

    @property
    def info_map(self)->np.array:
        return self.board.info_map

    @property
    def game_n_mines(self)->int:
        '''整个游戏雷的个数'''
        return self.board.num_mines

    @property
    def n_flags(self)->int:
        return (self.info_map==9).sum()

    @property
    def n_blanks(self)->int:
        return (self.info_map==11).sum()

    def blank_ceils(self)->Iterator[Ceil]:
        yy, xx = np.where(self.info_map==11)
        for x, y in zip(xx, yy):
            yield Ceil(x, y, self.board)

    def num_ceils(self)->Iterator[Ceil]:
        # print('info_map:', self.info_map)
        yy, xx = np.where(self.info_map<9)
        for x, y in zip(xx, yy):
            # print('num ceil:', x, y)
            yield Ceil(x, y, self.board)

    def random_conner_blank_ceil(self)->Ceil:
        ceils = [
            Ceil(0, 0, self.board),
            Ceil(self.board.board_width-1, 0, self.board),
            Ceil(0, self.board.board_height-1, self.board),
            Ceil(self.board.board_width-1, self.board.board_height-1, self.board),
        ]
        ceils = [c for c in ceils if c.is_blank]
        return random.choice(ceils)


    def usefull_num_ceils(self)->Iterator[Ceil]:
        for nc in self.num_ceils():
            if nc in self.useless_ceils:
                continue
            elif nc.is_useless_num:
                self.useless_ceils.append(nc)
                continue
            yield nc


    def rule_groups(self)->list:
        for nc in self.num_ceils():
            if (nc.x, nc.y) in self.useless_ceils:
                continue
            if nc.is_useless_num:
                self.useless_ceils.append((nc.x, nc.y))
                continue
        
    def one_rule_best(self):
        nceils = 0
        ceils = []
        for ceil in self.usefull_num_ceils():
            # print('usefull ceil:', ceil)
            nceils += 1
            if ceil.is_arounded_mines:
                # print('all are mines:', ceil)
                return 'flag', ceil.around_blank_ceils
            elif ceil.is_arounded_nums:
                # print('all are nums:', ceil)
                return 'click', ceil.around_blank_ceils
            else:
                ceils.append(ceil)
        if nceils == 0:
            return 'click', set([Ceil(0, 0, self.board)])
        return 'rules', ceils

    
    def probability_least_ceil(self, ceils: List[Ceil])->Ceil:
        probs = dict()
        best_ceil = None
        least_pro  = 1
        for c in ceils:
            for ab in c.around_blank_ceils:
                if ab in probs:
                    if probs[ab] < c.around_mine_pro:
                        probs[ab] = c.around_mine_pro
                else:
                    probs[ab] = c.around_mine_pro
        for c, pro in probs.items():
            if pro < least_pro:
                best_ceil = c
                least_pro = pro
        nb = self.n_blanks - len(probs)
        if nb == 0:
            return best_ceil
        nm = self.game_n_mines - self.n_flags - sum(probs.values())
        # print('least_pro:', least_pro)
        # print('left pro:', nm/nb)
        if nm/nb > least_pro:
            return best_ceil
        for bc in self.blank_ceils():
            if bc in probs:
                continue
            else:
                if bc.is_blank and bc not in probs:
                    # print('left blank ceil:', bc, bc not in probs)
                    # print('probs:', probs)
                    return bc

    def _all_same_ceils(self, allceils: list, mineceil_groups: list):
        mines = []
        nones = []
        for c in allceils:
            sm = 0
            for group in mineceil_groups:
                sm += (c in group)
            if sm == 0:
                nones.append(c)
            elif sm == len(mineceil_groups):
                mines.append(c)
        return mines, nones
            
        
    
    def more_rules_best(self, ceils: List[Ceil]):
        actions = []
        for c1 in ceils:
            i = ceils.index(c1)
            if i == len(ceils)-1:
                continue
            for c2 in ceils[i+1:]:
                abc1, abc2 = set(c1.around_blank_ceils), set(c2.around_blank_ceils)
                if abc1 == abc2:
                    continue
                join = abc1 & abc2
                if len(join)==0:
                    continue
                answers = []
                for cbn1 in combinations(abc1, c1.n_left_mines): # 被抽出来的就是雷
                    cbn1 = set(cbn1)
                    for cbn2 in combinations(abc2, c2.n_left_mines):
                        cbn2 = set(cbn2)
                        if (cbn1&join) == (cbn2&join): # 共享的cell必须值相同
                            answers.append(cbn1|cbn2)
                assert len(answers)
                allceils = abc1 | abc2
                mines, nones = self._all_same_ceils(allceils, answers)
                for c in mines:
                    actions.append(('flag', c.x, c.y))
                for c in nones:
                    actions.append(('click', c.x, c.y))
                if actions:
                    print('two rule actions:', actions)
                    return actions
        best = self.probability_least_ceil(ceils)
        # print('guess random ceils.......', best)
        self.board.print_board()
        return [('click', best.x, best.y)] 
       

    def best_move(self)->tuple:
        move, ceils = self.one_rule_best()
        if move != 'rules':
            # print(move, ceils)
            return [(move, c.x, c.y) for c in ceils]
        # print('Oh not single rule to use...............')
        self.board.print_board()
        return self.more_rules_best(ceils)
        



class Bot(QtCore.QThread):
    """Thread that covers remote control."""

    transfer = QtCore.pyqtSignal("QString")

    def __init__(self, seconds=62):
        """Init function of the thread."""
        super(Bot, self).__init__()
        self.exiting = False
        self.n_suc = 0
        self.n_los = 0
        self.seconds = seconds

    def __del__(self):
        """Destroy the thread."""
        self.exiting = True
        self.wait()

    def control_start(self, game: MSGame, grid):
        """Start thread control."""
        self.game = game
        self.grid = grid
        self.brain = Brain(game)
        self.start()
        self.clicker = Cliker(game.board_width, game.board_height)
        self.start_time = time.time()
        # self.clicker.start_timer()

    def wait_move(self, pre_num):
        while pre_num == self.game.num_moves:
            time.sleep(0.1)

    def run(self):
        """Thread behavior.
        game_status
        0: lose, 1: win, 2: playing
        """
        self.sleep(1)
        self.clicker.start_game()
        while self.game.game_status==2:
            moves = self.brain.best_move()
            for move in moves:
                pre_num = self.game.num_moves
                # self.sleep(10000)
                self.clicker.click(*move)
                self.wait_move(pre_num)
                if self.seconds < time.time() - self.start_time:
                    self.clicker.end_timer()
                    return
        if self.game.game_status == 1:
            self.n_suc += 1
        if self.game.game_status == 0:
            self.n_los += 1
        print('============================')
        print('suc:', self.n_suc, 'los:', self.n_los)
        print('============================')
        # self.game.reset_game()
        self.brain = Brain(self.game)
        self.clicker = Cliker(self.game.board_width, self.game.board_height)
        self.run()
    



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
    bot = Bot()
    def move(msg):
        if ms_game.game_status == 2:
            ms_game.play_move_msg(msg)
            grid_wg.update_grid()
    bot.transfer.connect(move)
    
    ms_window.show()
    bot.control_start(ms_game, grid_wg)
    bot.clicker.start_timer()
    
    ms_app.exec_()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Mine Sweeper Minesweeper \
                                                  with interfaces for \
                                                  Reinforcement Learning \
                                                  by Yuhuang Hu")
    parser.add_argument("--board-width", type=int,
                        default=9,
                        help="width of the board.")
    parser.add_argument("--board-height", type=int,
                        default=9,
                        help="height of the board.")
    parser.add_argument("--num-mines", type=int,
                        default=10,
                        help="number of mines.")
    parser.add_argument("--port", type=int,
                        default=5678,
                        help="The port for TCP connection.")
    parser.add_argument("--ip-add", type=str,
                        default="127.0.0.1",
                        help="The IP address for TCP connection.")
    args = parser.parse_args()
    ms_game_main(**vars(args))
    


    