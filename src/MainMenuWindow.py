from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, \
    QPushButton, QLabel, QLineEdit, QComboBox, QApplication
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush
from MainMenu import Ui_Form
import random


class MainMenuWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Создаем основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Создаем контейнер для UI из Qt Designer
        self.ui_container = QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.ui_container)

        # Добавляем UI контейнер в основной layout
        main_layout.addWidget(self.ui_container)

        screen = QApplication.primaryScreen()
        screen_size = screen.availableSize()
        font_size = max(10, screen_size.height() // 80)

        table_font = self.ui.tableWidget.font()
        table_font.setPointSize(font_size)
        self.ui.tableWidget.setFont(table_font)

        # Также настройте шрифт для кнопок
        button_font = self.ui.pushButton.font()
        button_font.setPointSize(font_size)
        self.ui.pushButton.setFont(button_font)
        self.ui.pushButton_2.setFont(button_font)
        self.ui.pushButton_3.setFont(button_font)
        self.ui.pushButton_4.setFont(button_font)

        # Установка заголовка
        self.setWindowTitle("Система мониторинга доменов")
        self.resize(1200, 800)  # Устанавливаем начальный размер

        # Подключение сигналов
        self.ui.pushButton.clicked.connect(self.show_top_failures)
        self.ui.pushButton_2.clicked.connect(self.show_my_domains)
        self.ui.pushButton_3.clicked.connect(self.show_add_data_dialog)
        self.ui.pushButton_4.clicked.connect(self.show_data)
        #кнопка показать данные
        # Дополнительная настройка таблицы
        self.setup_table()

        # Загрузка данных по умолчани

        self.ui.tableWidget.hide()
        self.table_visible = False  # Добавьте эту строку

        # Обновление стилей кнопок
        self.update_button_styles('my_domains')

        # Установите правильные стили для всех кнопок
        self.update_all_button_styles()  # Добавьте эту строку
        self.show_my_domains()

    def setup_table(self):
        """Дополнительная настройка таблицы"""
        self.ui.tableWidget.setAlternatingRowColors(True)
        self.ui.tableWidget.setSelectionBehavior(QHeaderView.SelectRows)
        self.ui.tableWidget.setSelectionMode(QHeaderView.SingleSelection)
        self.ui.tableWidget.setSortingEnabled(True)

        # Устанавливаем растягивание таблицы
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_my_domains(self):
        """Отображение данных 'Мои домены'"""
        # Настройка таблицы
        if not self.table_visible:
            return
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setHorizontalHeaderLabels(
            ['Домен', 'Статус', 'Трафик', 'Время ответа', 'Последняя проверка'])

        # Данные для "Мои домены"
        domains_data = [
            ['example.com', 'Активен', '1500', '120ms', '2024-01-15 10:30'],
            ['test-site.ru', 'Неактивен', '250', 'N/A', '2024-01-15 09:45'],
            ['my-domain.org', 'Активен', '4200', '85ms', '2024-01-15 11:20'],
            ['shop-site.com', 'Ошибка', '1800', '350ms', '2024-01-15 10:15'],
            ['blog-platform.net', 'Активен', '3100', '95ms', '2024-01-15 12:00'],
            ['api-service.io', 'Активен', '2750', '110ms', '2024-01-15 11:45'],
            ['data-center.org', 'Обслуживание', '950', 'N/A', '2024-01-15 08:30']
        ]

        # Заполнение таблицы с цветовым кодированием
        self.ui.tableWidget.setRowCount(len(domains_data))

        for row, data in enumerate(domains_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)

                item_font = item.font()
                item_font.setPointSize(max(10, self.height() // 80))
                item.setFont(item_font)

                # Цветовое кодирование статусов
                if col == 1:  # Колонка статуса
                    if value == 'Активен':
                        item.setBackground(QBrush(QColor(0, 128, 0, 100)))  # Зеленый
                    elif value == 'Ошибка':
                        item.setBackground(QBrush(QColor(255, 0, 0, 100)))  # Красный
                    elif value == 'Неактивен':
                        item.setBackground(QBrush(QColor(128, 128, 128, 100)))  # Серый
                    elif value == 'Обслуживание':
                        item.setBackground(QBrush(QColor(255, 165, 0, 100)))  # Оранжевый

                self.ui.tableWidget.setItem(row, col, item)

        # Настройка ширины колонок
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        # Обновление стиля кнопок
        self.update_button_styles('my_domains')

    def show_top_failures(self):
        """Отображение данных 'Топ сбоев'"""
        # Настройка таблицы
        if not self.table_visible:
            return
        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(['Домен', 'Количество ошибок', 'Последняя ошибка', 'Критичность'])

        # Данные для "Топ сбоев"
        failures_data = [
            ['example.com', '15', '2024-01-15 10:30', 'Высокая'],
            ['shop-site.com', '12', '2024-01-14 16:45', 'Высокая'],
            ['api-service.io', '8', '2024-01-13 09:20', 'Средняя'],
            ['test-site.ru', '5', '2024-01-12 14:15', 'Средняя'],
            ['data-center.org', '3', '2024-01-11 11:00', 'Низкая'],
            ['blog-platform.net', '2', '2024-01-10 08:45', 'Низкая'],
            ['my-domain.org', '1', '2024-01-09 17:30', 'Низкая']
        ]

        # Заполнение таблицы с цветовым кодированием
        self.ui.tableWidget.setRowCount(len(failures_data))

        for row, data in enumerate(failures_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)

                item_font = item.font()
                item_font.setPointSize(max(10, self.height() // 80))
                item.setFont(item_font)

                # Цветовое кодирование критичности
                if col == 3:  # Колонка критичности
                    if value == 'Высокая':
                        item.setBackground(QBrush(QColor(255, 0, 0, 100)))  # Красный
                    elif value == 'Средняя':
                        item.setBackground(QBrush(QColor(255, 165, 0, 100)))  # Оранжевый
                    elif value == 'Низкая':
                        item.setBackground(QBrush(QColor(0, 128, 0, 100)))  # Зеленый

                self.ui.tableWidget.setItem(row, col, item)

        # Настройка ширины колонок
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Обновление стиля кнопок
        self.update_button_styles('top_failures')

    def show_add_data_dialog(self):
        """Диалог добавления новых данных"""
        dialog = QWidget()
        dialog.setWindowTitle("Добавить новый домен")
        dialog.setFixedSize(800, 800)
        dialog.setStyleSheet("""
            QWidget {
                background-color: rgba(16, 30, 41, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
                margin-top: 10px;
            }
            QLineEdit, QComboBox {
                background-color: rgba(25, 45, 60, 200);
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 8px;
                color: white;
                margin-bottom: 10px;
            }
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Поля формы
        domain_label = QLabel("Домен:")
        domain_input = QLineEdit()
        domain_input.setPlaceholderText("example.com")

        status_label = QLabel("Статус:")
        status_combo = QComboBox()
        status_combo.addItems(["Активен", "Неактивен", "Ошибка", "Обслуживание"])

        traffic_label = QLabel("Трафик:")
        traffic_input = QLineEdit()
        traffic_input.setPlaceholderText("1000")

        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        cancel_button = QPushButton("Отмена")

        add_button.clicked.connect(lambda: self.add_new_domain(
            domain_input.text(),
            status_combo.currentText(),
            traffic_input.text(),
            dialog
        ))
        cancel_button.clicked.connect(dialog.close)

        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)

        # Добавление виджетов в layout
        layout.addWidget(domain_label)
        layout.addWidget(domain_input)
        layout.addWidget(status_label)
        layout.addWidget(status_combo)
        layout.addWidget(traffic_label)
        layout.addWidget(traffic_input)
        layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.show()

    def add_new_domain(self, domain, status, traffic, dialog):
        """Добавление нового домена"""
        if not domain:
            QMessageBox.warning(self, "Ошибка", "Введите доменное имя")
            return

        try:
            traffic_int = int(traffic) if traffic else 0
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Трафик должен быть числом")
            return

        # Добавление в таблицу (упрощенная версия)
        QMessageBox.information(self, "Успех", f"Домен {domain} добавлен успешно!")
        dialog.close()

        # Обновляем таблицу
        if self.ui.pushButton_2.styleSheet().find("rgba(2, 65, 118, 255)") != -1:
            self.show_my_domains()
        else:
            self.show_top_failures()

    def update_button_styles(self, active_tab):
        """Обновление стилей кнопок для визуального выделения активной вкладки"""
        active_style = """
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 255);
                border-radius: 5px;
                font-weight: bold;
                border: 2px solid rgba(0, 125, 236, 255);
                padding: 10px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 150);
            }
        """

        inactive_style = """
            QPushButton {
                background-color: rgba(2, 65, 118, 150);
                color: rgba(255, 255, 255, 180);
                border-radius: 5px;
                border: 2px solid transparent;
                padding: 10px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 150);
            }
        """

        if active_tab == 'my_domains':
            self.ui.pushButton_2.setStyleSheet(active_style)
            self.ui.pushButton.setStyleSheet(inactive_style)
        else:
            self.ui.pushButton.setStyleSheet(active_style)
            self.ui.pushButton_2.setStyleSheet(inactive_style)

        # Сохраняем стили для кнопок "Добавить данные" и "Показать данные"
        other_buttons_style = """
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 10px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 100);
            }
        """
        self.ui.pushButton_3.setStyleSheet(other_buttons_style)
        self.ui.pushButton_4.setStyleSheet(other_buttons_style)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите выйти?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def show(self):
        """Переопределение show для центрирования окна"""
        super().show()
        # Центрирование окна на экране
        frame_geometry = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)

        # Динамическое изменение размера шрифта
        font_size = max(10, self.height() // 80)

        # Обновляем шрифт таблицы
        table_font = self.ui.tableWidget.font()
        table_font.setPointSize(font_size)
        self.ui.tableWidget.setFont(table_font)

        # Обновляем шрифт кнопок
        button_font = self.ui.pushButton.font()
        button_font.setPointSize(font_size)
        self.ui.pushButton.setFont(button_font)
        self.ui.pushButton_2.setFont(button_font)
        self.ui.pushButton_3.setFont(button_font)
        self.ui.pushButton_4.setFont(button_font)

    def show_data(self):
        """Обработка кнопки 'Показать данные' - переключает видимость таблицы"""
        if self.table_visible:
            # Скрываем таблицу
            self.ui.tableWidget.hide()
            self.ui.pushButton_4.setText("Показать данные")  # Меняем текст кнопки
            self.table_visible = False
        else:
            # Показываем таблицу и обновляем данные
            self.ui.tableWidget.show()
            self.ui.pushButton_4.setText("Скрыть данные")  # Меняем текст кнопки
            self.table_visible = True

            # Обновляем текущую таблицу
            if self.ui.pushButton_2.styleSheet().find("rgba(2, 65, 118, 255)") != -1:
                self.show_my_domains()
            else:
                self.show_top_failures()

    def update_all_button_styles(self):
        """Обновление стилей всех кнопок"""
        base_style = """
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 10px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 100);
            }
        """

        # Применяем базовый стиль ко всем кнопкам
        self.ui.pushButton.setStyleSheet(base_style)
        self.ui.pushButton_2.setStyleSheet(base_style)
        self.ui.pushButton_3.setStyleSheet(base_style)
        self.ui.pushButton_4.setStyleSheet(base_style)

