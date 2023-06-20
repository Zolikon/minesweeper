import sys

from PySide6.QtWidgets import QApplication
from app import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow(app)
    main.show()
    app.exec()
