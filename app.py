from PySide6.QtCore import QSettings

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout, QWidget, QVBoxLayout, \
    QHBoxLayout

import random

from components import MineDisplay, Timer, BestTimes, PlayButton, About

settings = QSettings('minesweeper', 'settings')
version = 1.0

class GameMode:

    def __init__(self, name, cols, rows, mines):
        self.name = name
        self.cols = cols
        self.rows = rows
        self.mines = mines


BEGINNER = GameMode('beginner', rows=10, cols=10, mines=10)
ADVANCED = GameMode('advanced', rows=20, cols=20, mines=50)
EXPERT = GameMode('expert', rows=16, cols=30, mines=99)



class Game(QWidget):

    def __init__(self, game_mode: GameMode):
        super().__init__()
        assert 0 < game_mode.mines < game_mode.cols * game_mode.rows
        self.rows = game_mode.rows
        self.cols = game_mode.cols
        self.mines = game_mode.mines
        self.game_mode = game_mode
        self.mine_display = MineDisplay(self.mines)
        self.timer = Timer()
        self.is_game_started = False
        self.is_game_ended = False
        self.game_button = QPushButton('🙂')
        self.game_button.setFixedSize(50, 50)
        self.game_button.setFont(QFont('Times', 25))
        self.game_button.clicked.connect(lambda _: self.parent().new_game())
        field = self.__generate_field()
        a = QVBoxLayout()
        info = QHBoxLayout()
        info.addWidget(self.mine_display)
        info.addWidget(self.game_button)
        info.addWidget(self.timer)
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
        field = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
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
            self.timer.on_game_start()
            self.is_game_started = True
        if not self.is_game_ended:
            self.check_for_win()

    def check_for_win(self):
        for i in self.buttons.values():
            if not (i.is_revealed or i.is_mine()):
                return
        self.on_win()

    def on_win(self):
        self.timer.on_win(self.game_mode.name)
        self.mine_display.on_win()
        self.game_button.setText('😎')
        for i in self.buttons.values():
            if i.is_mine():
                i.set_as_correctly_flagged_mine()
        self.on_game_end()

    def on_reveal(self, r, c):
        if self.buttons[(r, c)].is_mine():
            self.on_game_over(r, c)
            return
        if self.buttons[(r, c)].is_revealed or self.buttons[(r, c)].flag == PlayButton.FLAGGED_AS_MINE:
            return
        value = self.buttons[(r, c)].reveal()
        if value == 0:
            for next_r, next_c in self.__get_neighbors(r, c):
                self.on_reveal(next_r, next_c)

    def on_game_end(self):
        self.timer.on_game_end()
        for btn in self.buttons.values():
            btn.on_game_end()

    def on_mine_flagged(self):
        self.mine_display.decrease()

    def on_mine_unflagged(self):
        self.mine_display.increase()

    def on_game_over(self, r, c):
        self.on_game_end()
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





class MainWindow(QMainWindow):

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("Minesweeper")
        self.setup_menu()
        self.last_game_mode = BEGINNER
        self.last_game = None
        self.new_game()

    def setup_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        new_game_action = file_menu.addAction("New Game")
        file_menu.addSeparator()
        beginner_action = file_menu.addAction("Beginner")
        beginner_action.setCheckable(True)
        beginner_action.setChecked(True)

        def beginner_trigger():
            game_mode_checked_trigger(beginner_action)
            self.new_game(BEGINNER)

        beginner_action.triggered.connect(beginner_trigger)
        advanced_action = file_menu.addAction("Advanced")
        advanced_action.setCheckable(True)

        def advanced_trigger():
            game_mode_checked_trigger(advanced_action)
            self.new_game(ADVANCED)

        advanced_action.triggered.connect(advanced_trigger)
        expert_action = file_menu.addAction("Expert")
        expert_action.setCheckable(True)

        def expert_trigger():
            game_mode_checked_trigger(expert_action)
            self.new_game(EXPERT)

        expert_action.triggered.connect(expert_trigger)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Quit")
        quit_action.triggered.connect(lambda _: self.app.quit())

        info_menu = menu.addMenu("Best times")
        best_times_action = info_menu.addAction("Show")
        best_times_action.triggered.connect(MainWindow.show_best_times)

        best_times_reset_action = info_menu.addAction("Reset")
        best_times_reset_action.triggered.connect(MainWindow.reset_best_times)

        about_menu = menu.addMenu("Info")
        about_action = about_menu.addAction("About")
        about_action.triggered.connect(MainWindow.show_about_menu)

        def new_game_trigger():
            [i for i in [beginner_action, advanced_action, expert_action] if i.isChecked()][0].trigger()

        new_game_action.triggered.connect(new_game_trigger)

        def game_mode_checked_trigger(action):
            action.setChecked(True)
            if beginner_action != action:
                beginner_action.setChecked(False)
            if advanced_action != action:
                advanced_action.setChecked(False)
            if expert_action != action:
                expert_action.setChecked(False)

    @staticmethod
    def show_best_times():
        BestTimes().exec()

    @staticmethod
    def show_about_menu():
        About(version).exec()

    @staticmethod
    def reset_best_times():
        settings.remove(BEGINNER.name)
        settings.remove(ADVANCED.name)
        settings.remove(EXPERT.name)

    def new_game(self, game_mode: GameMode = None):
        game_mode_changed = False
        if game_mode and self.last_game_mode != game_mode:
            self.last_game_mode = game_mode
            game_mode_changed = True

        if self.centralWidget():
            self.centralWidget().destroy()
        self.setCentralWidget(
            Game(self.last_game_mode)
        )
        if game_mode_changed:
            self.adjustSize()
