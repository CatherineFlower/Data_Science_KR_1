from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, \
    QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from login import Ui_Form
import db


class LoginWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка UI из login.py
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Подключение сигналов
        self.ui.pushButton.clicked.connect(self.login)
        self.ui.pushButton_2.clicked.connect(self.create_account)

        # Установка адаптивного стиля
        self.setWindowTitle("Вход в систему")
        self.setupAdaptiveLayout()
        self.showFullScreen()     # Полноэкранный режим

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

        # Удаляем splitter_3 из текущего layout (если он там есть)
        if self.ui.splitter_3.parent():
            self.ui.splitter_3.parent().layout().removeWidget(self.ui.splitter_3)

        # Добавляем splitter_3 в центр
        center_layout.addWidget(self.ui.splitter_3)
        center_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Добавляем центральный layout в главный
        main_layout.addLayout(center_layout)

        # Добавляем растягивающееся пространство снизу
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Настраиваем растягивание внутри splitter'ов
        self.ui.splitter_3.setStretchFactor(0, 1)  # label_2 (иконка)
        self.ui.splitter_3.setStretchFactor(1, 2)  # splitter_2 (поля ввода)
        self.ui.splitter_3.setStretchFactor(2, 1)  # splitter (кнопки)

        # Устанавливаем минимальные размеры
        self.ui.splitter_3.setMinimumSize(800, 800)

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
        text_font_size = max(16, min(16, width // 80, height // 50))

        text_font = self.ui.lineEdit.font()
        text_font.setPointSize(text_font_size)
        self.ui.lineEdit.setFont(text_font)
        self.ui.lineEdit_2.setFont(text_font)

        button_font = self.ui.pushButton.font()
        button_font.setPointSize(text_font_size)
        self.ui.pushButton.setFont(button_font)
        self.ui.pushButton_2.setFont(button_font)

        # Адаптивные отступы для кнопок
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
        self.ui.pushButton.setStyleSheet(button_style)
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

    def login(self):
        # Попытка поднять админа из .env, если схема уже создана
        try:
            db.ensure_admin_from_env()
        except Exception:
            pass

        username = self.ui.lineEdit.text().strip()
        password = self.ui.lineEdit_2.text()

        if not username or not password:
            self.showMessage("Ошибка", "Заполните все поля!", 'warning')
            return

        try:
            user = db.authenticate(username, password)
        except Exception as e:
            self.showMessage("Ошибка", f"Проблема с БД: {e}", 'error')
            return

        if user:
            self.showMessage("Успех", "Вход выполнен успешно!", 'info')
            self.close()
            from MainMenuWindow import MainMenuWindow
            self.main_window = MainMenuWindow(user=user)
            self.main_window.showMaximized()
        else:
            self.showMessage("Ошибка", "Неверные логин/пароль.", 'warning')

    def create_account(self):
        from CreateUserWindow import CreateUserWindow
        self.create_window = CreateUserWindow()
        self.create_window.showMaximized()
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
