from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox, QVBoxLayout, QWidget, QHBoxLayout, \
    QPushButton, QLabel, QLineEdit, QComboBox, QApplication
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog
from AdminDesign import Ui_Form
import db
from alter_table_dialog import AlterTableDialog
from select_builder_dialog import SelectBuilderDialog
from string_funcs_dialog import StringFuncsDialog
from join_wizard_dialog import JoinWizardDialog
from user_types_dialog import UserTypesDialog
from text_search_dialog import TextSearchDialog


class AdminDesignWindow(QMainWindow):
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

        # Настройка шрифта для кнопок
        button_font = self.ui.createSchemaButton.font()
        button_font.setPointSize(font_size)

        # Устанавливаем шрифт для всех кнопок
        for button in [
            self.ui.createSchemaButton, self.ui.deleteSchemaButton, self.ui.btnAlterTable, self.ui.btnSelect, self.ui.btnUserTypes, self.ui.btnTextSearch
        ]:
            button.setFont(button_font)

        # Установка заголовка
        self.setWindowTitle("Меню Администратора")
        self.resize(1200, 800)

        # Подключение сигналов
        self.ui.createSchemaButton.clicked.connect(self.do_create)
        self.ui.deleteSchemaButton.clicked.connect(self.do_drop)
        self.ui.btnAlterTable.clicked.connect(lambda: AlterTableDialog(self, schema="app").exec_())
        self.ui.btnSelect.clicked.connect(lambda: SelectBuilderDialog(self, schema="app").exec_())
        self.ui.btnStringFunc.clicked.connect(lambda: StringFuncsDialog(self, schema="app").exec_())
        self.ui.btnMasterJoin.clicked.connect(lambda: JoinWizardDialog(self, schema="app").exec_())
        self.ui.btnUserTypes.clicked.connect(lambda: UserTypesDialog(parent=self, schema="app").exec_())
        self.ui.btnTextSearch.clicked.connect(lambda: TextSearchDialog(parent=self, schema="app").exec_())
        self.ui.btnBackMain.clicked.connect(self.do_back)

    def show(self):
        """Переопределение show для центрирования окна"""
        super().show()
        # Центрирование окна на экране
        frame_geometry = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def do_create(self):
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

    def do_drop(self):
        ret = QMessageBox.question(self, "Подтверждение", "Удалить схему app? Данные будут потеряны.",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            try:
                db.drop_schema("app")
                QMessageBox.information(self, "OK", "Схема удалена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))



    def do_back(self):
        if self.parent():
            self.parent().user = self.user
            self.parent().show()
        self.close()





