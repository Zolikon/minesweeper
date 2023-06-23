from PySide6 import QtCore
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QLCDNumber, QMessageBox, QPushButton

settings = QSettings('minesweeper', 'settings')

MINE_ICON = '💣'
FLAG_ICON = '🚩'
QUESTION_ICON = '❓'


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

    def on_game_start(self):
        self.timer.start(1000)

    def on_game_end(self):
        self.timer.stop()

    def on_win(self, game_mode_name):
        last_best_time = settings.value(game_mode_name, 999)
        if self.count < last_best_time:
            settings.setValue(game_mode_name, self.count)


class BestTimes(QMessageBox):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Best times")
        self.setText(f"""
        Beginner: {settings.value('beginner', 999)} seconds
        Advanced: {settings.value('advanced', 999)} seconds
        Expert:   {settings.value('expert', 999)}   seconds
        """)


class About(QMessageBox):

    def __init__(self, version):
        super().__init__()
        self.setWindowTitle("Minesweeper")
        self.setIcon(QMessageBox.Icon.Information)
        self.setText(f"""
        Version: {version}

        Source code: https://github.com/Zolikon/minesweeper
        """)


class MineDisplay(QLCDNumber):

    def __init__(self, mines):
        super().__init__()
        self.mines = mines
        self.display(self.mines)
        self.setStyleSheet(f'background-color:black;color:white;')

    def decrease(self):
        self.mines -= 1
        self.display(self.mines)

    def increase(self):
        self.mines += 1
        self.display(self.mines)

    def on_win(self):
        self.mines = 0
        self.display(self.mines)


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
        self.is_game_end = False
        self.setFixedSize(25, 25)

    def reveal(self):
        if self.is_mine():
            if self.flag != PlayButton.FLAGGED_AS_MINE:
                self.parent().on_game_over(self.row, self.col)
            return
        self.setText(str(self.value if self.value > 0 else ''))
        self.is_revealed = True
        self.set_background_color('rgb(25, 191, 180)')
        return self.value

    def on_game_end(self):
        self.is_game_end = True

    def mousePressEvent(self, e: QMouseEvent):
        if not self.is_game_end:
            if e.button() == QtCore.Qt.MouseButton.RightButton and not self.is_revealed:
                self.toggle_flag()
            elif e.button() == QtCore.Qt.MouseButton.LeftButton and self.is_clickable():
                self.parent().on_reveal(self.row, self.col)
            elif e.button() == QtCore.Qt.MouseButton.LeftButton and self.is_revealed:
                self.parent().on_reveal_neighbors_for_revealed(self.row, self.col)
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
            self.parent().on_mine_flagged()
        elif self.flag == self.FLAGGED_AS_QUESTION_MARK:
            self.setText(QUESTION_ICON)
            self.parent().on_mine_unflagged()

    def is_mine(self):
        return self.value == -1

    def __str__(self):
        return f'{self.row}:{self.col}'
