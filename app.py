from PySide6 import QtCore
from PySide6.QtCore import QTimer

from PySide6.QtGui import QMouseEvent, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout, QWidget, QVBoxLayout, \
    QHBoxLayout, QLCDNumber

import random

from event import EventHandler


MINE_ICON = '💣'
FLAG_ICON = '🚩'
QUESTION_ICON = '❓'


class GameMode:

    def __init__(self, cols, rows, mines):
        self.cols = cols
        self.rows = rows
        self.mines = mines


BEGINNER = GameMode(rows=10, cols=10, mines=10)
ADVANCED = GameMode(rows=20, cols=20, mines=50)
EXPERT = GameMode(rows=30, cols=30, mines=200)


@EventHandler.register()
class MineDisplay(QLCDNumber):

    def __init__(self, mines):
        super().__init__()
        self.mines = mines
        self.display(self.mines)
        self.setStyleSheet(f'background-color:black;color:white;')

    @EventHandler.capture_event('mine_marked')
    def decrease(self):
        self.mines -= 1
        self.display(self.mines)

    @EventHandler.capture_event('mine_unmarked')
    def increase(self):
        self.mines += 1
        self.display(self.mines)

    @EventHandler.capture_event('win')
    def win(self):
        self.mines = 0
        self.display(self.mines)


@EventHandler.register()
class Timer(QLCDNumber):

    def __init__(self):
        super().__init__()
        self.count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_counter)
        self.setStyleSheet(f'background-color:black;color:white;')
        self.show_counter()

    def show_counter(self):
        self.display(str(self.count).rjust(3, '0'))

    def update_counter(self):
        if self.count < 999:
            self.count += 1
        self.show_counter()

    @EventHandler.capture_event('game_start')
    def on_game_start(self):
        self.timer.start(1000)

    @EventHandler.capture_event('game_end')
    def on_game_end(self):
        self.timer.stop()


@EventHandler.register()
class Game(QWidget):

    def __init__(self, cols=10, rows=10, mines=10):
        super().__init__()
        assert 0 < mines < cols * rows
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.mine_display = MineDisplay(self.mines)
        self.is_game_started = False
        self.is_game_ended = False
        self.game_button = QPushButton('🙂')
        self.game_button.setFixedSize(50, 50)
        self.game_button.setFont(QFont('Times', 25))
        self.game_button.clicked.connect(lambda _: self.emit_event('new_game'))
        field = self.__generate_field()
        a = QVBoxLayout()
        info = QHBoxLayout()
        info.addWidget(self.mine_display)
        info.addWidget(self.game_button)
        info.addWidget(Timer())
        a.addLayout(info)

        self.buttons = {}
        layout = QGridLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        for r in range(self.rows):
            for c in range(self.cols):
                btn = PlayButton(r, c, field[r][c])
                btn.set_background_color('rgb(237, 255, 254)')
                self.buttons[(r, c)] = btn
                layout.addWidget(btn, r, c)
        a.addLayout(layout)
        self.setLayout(a)

    def __generate_field(self):
        def __add_mine(row, col):
            def inc_counter(neighbor_row, neighbor_col):
                if 0 <= neighbor_row < self.rows and 0 <= neighbor_col < self.cols:
                    if not field[neighbor_row][neighbor_col] == -1:
                        field[neighbor_row][neighbor_col] += 1

            if field[row][col] == -1:
                return False
            field[row][col] = -1

            for neighbor in self.__get_neighbors(row, col):
                inc_counter(*neighbor)
            return True

        current_mines = 0
        field = [[0 for r in range(self.rows)] for c in range(self.cols)]
        while current_mines < self.mines:
            if __add_mine(random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)):
                current_mines += 1

        return field

    def __get_neighbors(self, row, col):
        def is_valid(r, c):
            return 0 <= r < self.rows and 0 <= c < self.cols

        candidates = [(row - 1, col), (row - 1, col + 1), (row - 1, col - 1),
                      (row, col + 1), (row, col - 1),
                      (row + 1, col), (row + 1, col + 1), (row + 1, col - 1)]
        for i in filter(lambda t: is_valid(*t), candidates):
            yield i

    def click_happened_on_field(self):
        if not self.is_game_started and not self.is_game_ended:
            self.emit_event('game_start')
            self.is_game_started = True
        if not self.is_game_ended:
            self.check_for_win()

    def check_for_win(self):
        for i in self.buttons.values():
            if not (i.is_revealed or i.is_mine()):
                return
        self.emit_event('win')

    @EventHandler.capture_event('win')
    def on_win(self):
        self.game_button.setText('😎')
        for i in self.buttons.values():
            if i.is_mine():
                i.set_as_correctly_flagged_mine()
        self.emit_event('game_end')

    @EventHandler.capture_event('reveal')
    def on_reveal(self, r, c):
        if self.buttons[(r, c)].is_mine():
            self.emit_event('game_over', r, c)
            return
        if self.buttons[(r, c)].is_revealed or self.buttons[(r, c)].flag == PlayButton.FLAGGED_AS_MINE:
            return
        value = self.buttons[(r, c)].reveal()
        if value == 0:
            for next_r, next_c in self.__get_neighbors(r, c):
                self.on_reveal(next_r, next_c)

    @EventHandler.capture_event('game_over')
    def on_game_over(self, r, c):
        self.emit_event('game_end')
        self.is_game_ended = True
        self.buttons[(r, c)].set_background_color('red')
        for b in self.buttons.values():
            if b.flag == PlayButton.FLAGGED_AS_MINE:
                if not b.is_mine():
                    b.set_as_false_mine()
                if b.is_mine():
                    b.set_as_correctly_flagged_mine()
            elif not b.is_revealed and b.is_mine():
                b.set_as_missed_mine()
        self.game_button.setText('😞')
        self.buttons.clear()

    @EventHandler.capture_event('reveal_neighbors_for_revealed')
    def on_reveal_neighbors_for_revealed(self, r, c):
        number_of_neighbor_marked_mines = len(
            [i for i in self.__get_neighbors(r, c) if self.buttons[i].flag == PlayButton.FLAGGED_AS_MINE])
        if number_of_neighbor_marked_mines == self.buttons[(r, c)].value:
            unrevealed_neighbors = [self.buttons[i] for i in self.__get_neighbors(r, c) if
                                    not self.buttons[i].is_revealed]
            for i in unrevealed_neighbors:
                if i.reveal() == 0:
                    self.reveal_neighbor_for_0_field(i.row, i.col)

    def reveal_neighbor_for_0_field(self, r, c):
        for new_r, new_c in self.__get_neighbors(r, c):
            if not self.buttons[(new_r, new_c)].is_revealed and self.buttons[(new_r, new_c)].reveal() == 0:
                self.reveal_neighbor_for_0_field(new_r, new_c)


@EventHandler.register()
class PlayButton(QPushButton):
    NO_FLAG = 0
    FLAGGED_AS_MINE = 1
    FLAGGED_AS_QUESTION_MARK = 2

    def __init__(self, row, col, value):
        super().__init__()
        self.row = row
        self.col = col
        self.value = value
        self.flag = self.NO_FLAG
        self.is_revealed = False
        self.setFixedSize(25, 25)

    def reveal(self):
        if self.is_mine():
            if self.flag != PlayButton.FLAGGED_AS_MINE:
                self.emit_event('game_over', self.row, self.col)
            return
        self.setText(str(self.value if self.value > 0 else ''))
        self.is_revealed = True
        self.set_background_color('rgb(25, 191, 180)')
        return self.value

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == QtCore.Qt.MouseButton.RightButton and not self.is_revealed:
            self.toggle_flag()
        elif e.button() == QtCore.Qt.MouseButton.LeftButton and self.is_clickable():
            self.emit_event('reveal', self.row, self.col)
        elif e.button() == QtCore.Qt.MouseButton.LeftButton and self.is_revealed:
            self.emit_event('reveal_neighbors_for_revealed', self.row, self.col)
        self.parent().click_happened_on_field()

    def set_as_false_mine(self):
        self.setText('!!!')
        self.set_background_color('red')

    def set_as_missed_mine(self):
        self.setText(MINE_ICON)
        self.set_background_color('red')

    def set_as_correctly_flagged_mine(self):
        self.setText(MINE_ICON)
        self.set_background_color('green')

    def set_background_color(self, color):
        self.setStyleSheet(f'background-color:{color};')

    def is_clickable(self):
        return self.flag != self.FLAGGED_AS_MINE and not self.is_revealed

    def toggle_flag(self):
        self.flag = self.flag + 1 if self.flag != self.FLAGGED_AS_QUESTION_MARK else self.NO_FLAG
        if self.flag == self.NO_FLAG:
            self.setText('')
        elif self.flag == self.FLAGGED_AS_MINE:
            self.setText(FLAG_ICON)
            self.emit_event('mine_marked')
        elif self.flag == self.FLAGGED_AS_QUESTION_MARK:
            self.setText(QUESTION_ICON)
            self.emit_event('mine_unmarked')

    def is_mine(self):
        return self.value == -1

    def __str__(self):
        return f'{self.row}:{self.col}'


@EventHandler.register()
class MainWindow(QMainWindow):

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("Minesweeper")
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        beginner_action = file_menu.addAction("Beginner")
        beginner_action.triggered.connect(lambda _: self.emit_event('new_game', BEGINNER))
        advanced_action = file_menu.addAction("Advanced")
        advanced_action.triggered.connect(lambda _: self.emit_event('new_game', ADVANCED))
        expert_action = file_menu.addAction("Expert")
        expert_action.triggered.connect(lambda _: self.emit_event('new_game', EXPERT))
        quit_action = file_menu.addAction("Quit")
        quit_action.triggered.connect(lambda _: self.app.quit())
        self.last_game_mode = BEGINNER
        self.last_game = None
        self.new_game()

    @EventHandler.capture_event('new_game')
    def new_game(self, game_mode: GameMode = None):
        game_mode_changed = False
        if game_mode and self.last_game_mode != game_mode:
            self.last_game_mode = game_mode
            game_mode_changed = True

        if self.last_game:
            self.last_game.unregister()
            self.last_game.destroy()

        self.last_game = Game(self.last_game_mode.rows, self.last_game_mode.cols, self.last_game_mode.mines)
        if self.centralWidget():
            self.centralWidget().destroy()
        self.setCentralWidget(
            self.last_game
        )
        if game_mode_changed:
            self.adjustSize()
