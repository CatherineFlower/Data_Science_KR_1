from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, \
    QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from CreateUser import Ui_Form


class CreateUserWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка UI из CreateUser.py
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Подключение сигналов
        self.ui.pushButton_2.clicked.connect(self.create_account)

        # Установка адаптивного стиля
        self.setWindowTitle("Создание аккаунта")
        self.setupAdaptiveLayout()
        self.showFullScreen()  # Полноэкранный режим

    def keyPressEvent(self, event):
        # Выход по ESC из полноэкранного режима
        if event.key() == Qt.Key_Escape:
            self.showNormal()  # Возврат к обычному режиму

    def setupAdaptiveLayout(self):
        """Настройка адаптивного layout поверх сгенерированного UI"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создаем главный вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # Добавляем растягивающееся пространство сверху
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Горизонтальный layout для центрирования
        center_layout = QHBoxLayout()
        center_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Удаляем splitter_2 из текущего layout (если он там есть)
        if self.ui.splitter_2.parent():
            self.ui.splitter_2.parent().layout().removeWidget(self.ui.splitter_2)

        # Добавляем splitter_2 в центр
        center_layout.addWidget(self.ui.splitter_2)
        center_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Добавляем центральный layout в главный
        main_layout.addLayout(center_layout)

        # Добавляем растягивающееся пространство снизу
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Настраиваем растягивание внутри splitter'ов
        self.ui.splitter_2.setStretchFactor(0, 1)  # label_2 (иконка)
        self.ui.splitter_2.setStretchFactor(1, 1)  # lineEdit (имя пользователя)
        self.ui.splitter_2.setStretchFactor(2, 1)  # lineEdit_2 (пароль)
        self.ui.splitter_2.setStretchFactor(3, 1)  # lineEdit_3 (подтверждение пароля)
        self.ui.splitter_2.setStretchFactor(4, 1)  # splitter (кнопка)

        # Устанавливаем минимальные размеры
        self.ui.splitter_2.setMinimumSize(800, 800)

    def resizeEvent(self, event):
        """Адаптация интерфейса при изменении размера окна"""
        super().resizeEvent(event)

        # Получаем размеры окна
        width = self.width()
        height = self.height()

        # Адаптивный размер шрифта для иконки
        icon_font = self.ui.label_2.font()
        icon_size = max(40, min(100, width // 15, height // 10))
        icon_font.setPointSize(icon_size)
        self.ui.label_2.setFont(icon_font)

        # Адаптивный размер шрифта для текста
        text_font_size = max(10, min(16, width // 80, height // 50))

        text_font = self.ui.lineEdit.font()
        text_font.setPointSize(text_font_size)
        self.ui.lineEdit.setFont(text_font)
        self.ui.lineEdit_2.setFont(text_font)
        self.ui.lineEdit_3.setFont(text_font)

        button_font = self.ui.pushButton_2.font()
        button_font.setPointSize(text_font_size)
        self.ui.pushButton_2.setFont(button_font)

        # Адаптивные отступы для кнопки
        button_padding = max(5, min(15, width // 100))
        button_style = f"""
            QPushButton {{
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: {button_padding}px;
                font-size: {text_font_size}px;
            }}
            QPushButton:pressed {{
                padding-left: {button_padding + 5}px;
                padding-top: {button_padding + 5}px;
                background-color: rgba(2, 65, 118, 100);
            }}
            QPushButton:hover {{
                background-color: rgba(2, 65, 118, 200);
            }}
        """
        self.ui.pushButton_2.setStyleSheet(button_style)

        # Адаптивные отступы для полей ввода
        input_style = f"""
            QLineEdit {{
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid rgba(0, 0, 0, 0);
                border-bottom-color: rgba(46, 82, 110, 255);
                color: rgb(255, 255, 255);
                padding: {max(8, button_padding)}px;
                font-size: {text_font_size}px;
            }}
        """
        self.ui.lineEdit.setStyleSheet(input_style)
        self.ui.lineEdit_2.setStyleSheet(input_style)
        self.ui.lineEdit_3.setStyleSheet(input_style)

    def create_account(self):
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()
        confirm_password = self.ui.lineEdit_3.text()

        if not username or not password or not confirm_password:
            self.showMessage("Ошибка", "Заполните все поля!", 'warning')
            return

        if password != confirm_password:
            self.showMessage("Ошибка", "Пароли не совпадают!", 'warning')
            return

        self.showMessage("Успех", f"Аккаунт '{username}' создан успешно!", 'info')
        from MainMenuWindow import MainMenuWindow
        self.mainMenu = MainMenuWindow()
        self.mainMenu.show()
        self.close()

    def showMessage(self, title, message, message_type='info'):
        """Кастомное сообщение с темным стилем"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)

        # Темный стиль для QMessageBox
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgba(25, 35, 45, 240);
                color: white;
                border: 2px solid rgba(46, 82, 110, 255);
                border-radius: 10px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QMessageBox QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QMessageBox QPushButton:pressed {
                background-color: rgba(2, 65, 118, 150);
            }
        """)

        if message_type == 'info':
            msg.setIcon(QMessageBox.Information)
        elif message_type == 'warning':
            msg.setIcon(QMessageBox.Warning)
        elif message_type == 'error':
            msg.setIcon(QMessageBox.Critical)

        msg.exec_()