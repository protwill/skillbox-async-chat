"""
Пример программы для работы с интерфейсами Qt
"""
from PySide2.QtWidgets import QMainWindow, QApplication

from src.day_03.interface import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.message_button.clicked.connect(self.button_handler)

    def button_handler(self):
        self.message_box.appendPlainText(
            self.message_input.text()
        )
        self.message_input.clear()


app = QApplication()
window = MainWindow()
window.show()
app.exec_()
