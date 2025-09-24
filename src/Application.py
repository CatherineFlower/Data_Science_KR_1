from PyQt5.QtWidgets import QApplication

class Application(QApplication):
    def __init__(self, argv): #создаем функцию конструктор класса
        super().__init__(argv) #вызываем конструктор базового класса


