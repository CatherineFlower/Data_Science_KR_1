from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, \
QPushButton, QLabel, QLineEdit, QComboBox, QApplication
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QBrush
from MainMenu import Ui_Form
import random
import db


class MainMenuWindow(QMainWindow):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user

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

                # Добавим кнопку Админ
        from PyQt5.QtWidgets import QPushButton
        self.adminButton = QPushButton('Админ')
        self.adminButton.clicked.connect(self.open_admin_panel)
        self.ui.horizontalLayout_top.addWidget(self.adminButton)
        
        self.btnRefresh = QPushButton("Обновить")
        self.btnDeleteDomain = QPushButton("Удалить домен")
        self.btnLogout = QPushButton("Выйти")
        self.btnDeleteProfile = QPushButton("Удалить профиль")

        self.btnRefresh.clicked.connect(self.refresh_current)
        self.btnDeleteDomain.clicked.connect(self.delete_selected_domain)
        self.btnLogout.clicked.connect(self.logout)
        self.btnDeleteProfile.clicked.connect(self.delete_profile)

        self.ui.horizontalLayout_top.addWidget(self.btnRefresh)
        self.ui.horizontalLayout_top.addWidget(self.btnDeleteDomain)
        self.ui.horizontalLayout_top.addWidget(self.btnLogout)
        self.ui.horizontalLayout_top.addWidget(self.btnDeleteProfile)

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
        """Отображение 'Мои домены' из БД"""
        self.ui.tableWidget.show()
        self.table_visible = True
        self.btnDeleteDomain.setEnabled(True)
        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(['Домен', 'Статус', 'Последнее изменение', 'Дата добавления'])
        rows = []
        try:
            if self.user and 'id' in self.user:
                rows = db.list_user_domains(self.user['id'])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"{e}")
            rows = []
        self.ui.tableWidget.setRowCount(len(rows))
        for r, d in enumerate(rows):
            vals = [d.get('domain',''), d.get('state',''), str(d.get('started_at') or ''), str(d.get('tracking_started') or '')]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignCenter)
                self.ui.tableWidget.setItem(r, c, item)
        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.update_button_styles('my_domains')

    def show_top_failures(self):
        """Топ сбоев за час + 'Отслеживают'"""
        self.ui.tableWidget.show()
        self.table_visible = True
        self.btnDeleteDomain.setEnabled(False)
        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(['Домен', 'Количество ошибок за час', 'Последняя ошибка', 'Отслеживают'])

        data = []
        try:
            data = db.list_top_failures(100)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"{e}")
            data = []

        self.ui.tableWidget.setRowCount(len(data))
        for row, d in enumerate(data):
            vals = [d.get('domain',''),
                    str(d.get('ddos_count_hour') or 0),
                    str(d.get('last_ddos_ts') or ''),
                    str(d.get('watchers') or 0)]
            for col, value in enumerate(vals):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.ui.tableWidget.setItem(row, col, item)

        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

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

        button_layout = QHBoxLayout()
        add_button = QPushButton("Добавить")
        cancel_button = QPushButton("Отмена")

        add_button.clicked.connect(lambda: self.add_new_domain(
            domain_input.text(),
            dialog
        ))
        cancel_button.clicked.connect(dialog.close)

        button_layout.addWidget(add_button)
        button_layout.addWidget(cancel_button)

        # Добавление виджетов в layout
        layout.addWidget(domain_label)
        layout.addWidget(domain_input)
        layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.show()

    def add_new_domain(self, domain, dialog):
        if not domain:
            QMessageBox.warning(self, "Ошибка", "Введите доменное имя"); return
        if not self.user or 'id' not in self.user:
            QMessageBox.critical(self, "Ошибка", "Нет информации о пользователе"); return
        dom = domain.strip().lower()
        try:
            db.add_domain(self.user['id'], dom)
        except Exception as e:
            # Попробуем автоматически поднять админа из .env и повторить (случай эпемерного админа после создания схемы)
            if self.user.get('ephemeral'):
                try:
                    new_admin = db.ensure_admin_from_env()
                    if new_admin:
                        self.user = new_admin
                        db.add_domain(self.user['id'], dom)
                    else:
                        raise e
                except Exception as e2:
                    QMessageBox.critical(self, "Ошибка БД", f"Не удалось добавить домен: {e2}"); return
            else:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось добавить домен: {e}"); return
        QMessageBox.information(self, "Успех", f"Домен {domain} добавлен.")
        dialog.close()
        self.show_my_domains()

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



    def open_admin_panel(self):
        if not self.user or not self.user.get('is_admin'):
            QMessageBox.warning(self, "Доступ запрещён", "Нужны права администратора.")
            return
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Администрирование")
        lay = QVBoxLayout(dlg)
        btn_create = QPushButton("Создать схему в БД")
        btn_drop = QPushButton("Удалить схему")
        lay.addWidget(btn_create)
        lay.addWidget(btn_drop)

        def do_create():
            try:
                cnt = db.create_schema("ddl.sql")
                # Если вход эфемерный - создаём существующий id админа в бд
                try:
                    new_admin = db.ensure_admin_from_env()
                    if new_admin:
                        self.user = new_admin
                except Exception:
                    pass
                QMessageBox.information(self, "OK", f"Схема создана. Выполнено операторов: {cnt}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

        def do_drop():
            ret = QMessageBox.question(self, "Подтверждение", "Удалить схему app? Данные будут потеряны.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.Yes:
                try:
                    db.drop_schema("app")
                    QMessageBox.information(self, "OK", "Схема удалена.")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))

        btn_create.clicked.connect(do_create)
        btn_drop.clicked.connect(do_drop)
        dlg.exec_()


    def domain_from_selected_row(self):
        r = self.ui.tableWidget.currentRow()
        if r < 0: return None
        item = self.ui.tableWidget.item(r, 0)
        return item.text().strip().lower() if item else None

    def delete_selected_domain(self):
        d = self.domain_from_selected_row()
        if not d:
            QMessageBox.warning(self, "Нет выбора", "Выберите домен в таблице."); return
        if not self.user or 'id' not in self.user:
            QMessageBox.critical(self, "Ошибка", "Нет информации о пользователе"); return
        ret = QMessageBox.question(self, "Подтверждение", f"Удалить домен {d} из ваших отслеживаемых?",
                                   QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes: return
        try:
            db.delete_domain_by_name(self.user['id'], d)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"{e}"); return
        self.refresh_current()

    def refresh_current(self):
        # простая логика: если колонок 4 и заголовок 0 == 'Домен' и 1 == 'Статус' -> мои домены
        if self.ui.tableWidget.columnCount() == 4:
            h0 = self.ui.tableWidget.horizontalHeaderItem(0)
            h1 = self.ui.tableWidget.horizontalHeaderItem(1)
            if h0 and h1 and h1.text() == 'Статус':
                self.show_my_domains(); return
        self.show_top_failures()

    def logout(self):
        from LoginWindow import LoginWindow
        self.close()
        self.loginWin = LoginWindow()
        self.loginWin.showMaximized()

    def delete_profile(self):
        if not self.user or 'id' not in self.user:
            QMessageBox.critical(self, "Ошибка", "Нет информации о пользователе"); return
        ret = QMessageBox.question(self, "Подтверждение", "Удалить ваш профиль и все ваши домены?",
                                   QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes: return
        try:
            db.delete_user(self.user['id'])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"{e}"); return
        self.logout()
    