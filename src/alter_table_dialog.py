from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QLineEdit, QPushButton, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import db
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp


class AlterTableDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("ALTER TABLE — конструктор")
        self.setMinimumWidth(700)  # Увеличили минимальную ширину
        self.setMinimumHeight(600)  # Добавили минимальную высоту

        # Создаем шрифт с увеличенным размером
        font = QFont()
        font.setPointSize(11)  # Увеличили размер шрифта

        self.setStyleSheet("""
            QDialog {
                background-color: rgba(16, 30, 41, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-size: 13px;
                padding: 8px;
            }
           QComboBox {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 12px;    
                min-height: 40px;  
                font-size: 24px;   
           }
            QComboBox:hover {
                border: 1px solid rgba(66, 122, 160, 255);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(25, 45, 60, 255);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                selection-background-color: rgba(2, 65, 118, 255);
                font-size: 14px;
                padding: 12px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 30px;  
                padding: 8px;      
            }
            QLineEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(66, 122, 160, 255);
            }
            QLineEdit::placeholder {
                color: rgba(200, 200, 200, 150);
                font-size: 12px;
            }
            QCheckBox {
                color: white;
                font-size: 13px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 3px;
                background-color: rgba(25, 45, 60, 200);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(2, 65, 118, 255);
            }
            QCheckBox::indicator:hover {
                border: 1px solid rgba(66, 122, 160, 255);
            }
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 12px;
                min-height: 40px;
                min-width: 120px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 100);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)  # Увеличили расстояние между элементами
        layout.setContentsMargins(20, 20, 20, 20)  # Увеличили отступы

        # Таблица
        hl = QHBoxLayout()
        label_table = QLabel("Таблица:")
        label_table.setFont(font)
        hl.addWidget(label_table)

        self.cbTable = QComboBox()
        self.cbTable.setFont(font)
        for sch, tbl in db.list_tables(schema):
            self.cbTable.addItem(f"{sch}.{tbl}", (sch, tbl))
        hl.addWidget(self.cbTable, 1)
        layout.addLayout(hl)

        # Действие
        self.cbAction = QComboBox()
        self.cbAction.setFont(font)
        self.cbAction.addItems([
            "ДОБАВИТЬ СТОЛБЕЦ",
            "УДАЛИТЬ СТОЛБЕЦ",
            "ПЕРЕИМЕНОВАТЬ СТОЛБЕЦ",
            "ИЗМЕНИТЬ ТИП",
            "ДОБАВИТЬ ОГРАНИЧЕНИЕ",
            "УДАЛИТЬ ОГРАНИЧЕНИЕ",
            "УСТАНОВИТЬ/СНЯТЬ NOT NULL",
            "УСТАНОВИТЬ/СНЯТЬ DEFAULT"
        ])
        layout.addWidget(self.cbAction)

        # Поля ввода
        self.edColName = QLineEdit()
        self.edColName.setFont(font)
        self.edColName.setPlaceholderText("Имя столбца")

        # В конструкторе после создания edColName:
        col_name_validator = QRegExpValidator(QRegExp("^[a-zA-Z_][a-zA-Z0-9_]{0,62}$"))
        self.edColName.setValidator(col_name_validator)

        self.edDataType = QLineEdit()
        self.edDataType.setFont(font)
        self.edDataType.setPlaceholderText("Тип, напр. text, integer")
        data_type_validator = QRegExpValidator(QRegExp("^[a-zA-Z]+(\\s*\\(\\s*\\d+\\s*(,\\s*\\d+\\s*)?\\))?$"))
        self.edDataType.setValidator(data_type_validator)

        self.edConstraint = QLineEdit()
        self.edConstraint.setFont(font)
        self.edConstraint.setPlaceholderText("Ограничение, напр. CHECK (...), UNIQUE, FOREIGN KEY (...) REFERENCES ...")

        self.edNewName = QLineEdit()
        self.edNewName.setFont(font)
        self.edNewName.setPlaceholderText("Новое имя столбца")
        self.edNewName.setValidator(col_name_validator)

        self.edDefault = QLineEdit()
        self.edDefault.setFont(font)
        self.edDefault.setPlaceholderText("DEFAULT-выражение")

        for w in (self.edColName, self.edDataType, self.edConstraint, self.edNewName, self.edDefault):
            layout.addWidget(w)

        # Чекбокс
        self.chkSet = QCheckBox("SET (если снять — будет DROP)")
        self.chkSet.setFont(font)
        self.chkSet.setChecked(True)
        layout.addWidget(self.chkSet)

        # Кнопки
        hb = QHBoxLayout()
        self.btnRun = QPushButton("Выполнить (транзакция)")
        self.btnRun.setFont(font)
        self.btnClose = QPushButton("Закрыть")
        self.btnClose.setFont(font)
        hb.addWidget(self.btnRun)
        hb.addStretch(1)
        hb.addWidget(self.btnClose)
        layout.addLayout(hb)

        self.cbAction.currentIndexChanged.connect(self._refresh)
        self.btnRun.clicked.connect(self.do_run)
        self.btnClose.clicked.connect(self.reject)
        self._refresh()

    def _refresh(self):
        act = self.cbAction.currentText()
        # Показывать/скрывать поля в зависимости от выбранного действия
        self.edColName.setVisible(
            act in ["ДОБАВИТЬ СТОЛБЕЦ", "УДАЛИТЬ СТОЛБЕЦ", "ПЕРЕИМЕНОВАТЬ СТОЛБЕЦ", "ИЗМЕНИТЬ ТИП",
                    "УСТАНОВИТЬ/СНЯТЬ NOT NULL", "УСТАНОВИТЬ/СНЯТЬ DEFAULT"])
        self.edDataType.setVisible(act in ["ДОБАВИТЬ СТОЛБЕЦ", "ИЗМЕНИТЬ ТИП"])
        self.edConstraint.setVisible(act in ["ДОБАВИТЬ ОГРАНИЧЕНИЕ", "УДАЛИТЬ ОГРАНИЧЕНИЕ"])
        self.edNewName.setVisible(act == "ПЕРЕИМЕНОВАТЬ СТОЛБЕЦ")
        self.edDefault.setVisible(act == "УСТАНОВИТЬ/СНЯТЬ DEFAULT")
        self.chkSet.setVisible(act in ["УСТАНОВИТЬ/СНЯТЬ NOT NULL", "УСТАНОВИТЬ/СНЯТЬ DEFAULT"])

    def do_run(self):
        (schema, table) = self.cbTable.currentData()
        act = self.cbAction.currentText()
        col = self.edColName.text().strip()
        dtype = self.edDataType.text().strip()
        cons = self.edConstraint.text().strip()
        newname = self.edNewName.text().strip()
        default = self.edDefault.text().strip()
        set_flag = self.chkSet.isChecked()
        full = f"{schema}.{table}"
        if act == "ДОБАВИТЬ СТОЛБЕЦ" and not self.edColName.hasAcceptableInput():
            QMessageBox.warning(self, "Ошибка", "Некорректное имя столбца")
            return

        if act == "ДОБАВИТЬ СТОЛБЕЦ" and not self.edDataType.hasAcceptableInput():
            QMessageBox.warning(self, "Ошибка", "Некорректный тип данных")
            return
        try:
            stmts = []
            if act == "ДОБАВИТЬ СТОЛБЕЦ":
                if not col or not dtype: raise ValueError("Укажите имя столбца и тип")
                stmts.append((f'ALTER TABLE {full} ADD COLUMN "{col}" {dtype}', ()))
            elif act == "УДАЛИТЬ СТОЛБЕЦ":
                if not col: raise ValueError("Укажите имя столбца")
                stmts.append((f'ALTER TABLE {full} DROP COLUMN "{col}"', ()))
            elif act == "ПЕРЕИМЕНОВАТЬ СТОЛБЕЦ":
                if not col or not newname: raise ValueError("Укажите имя столбца и новое имя")
                stmts.append((f'ALTER TABLE {full} RENAME COLUMN "{col}" TO "{newname}"', ()))
            elif act == "ИЗМЕНИТЬ ТИП":
                if not col or not dtype: raise ValueError("Укажите имя столбца и тип")
                stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" TYPE {dtype}', ()))
            elif act == "ДОБАВИТЬ ОГРАНИЧЕНИЕ":
                if not cons: raise ValueError("Укажите выражение/имя ограничения")
                stmts.append((f'ALTER TABLE {full} ADD {cons}', ()))
            elif act == "УДАЛИТЬ ОГРАНИЧЕНИЕ":
                if not cons: raise ValueError("Укажите имя ограничения")
                stmts.append((f'ALTER TABLE {full} DROP CONSTRAINT {cons}', ()))
            elif act == "УСТАНОВИТЬ/СНЯТЬ NOT NULL":
                if not col: raise ValueError("Укажите имя столбца")
                kw = "SET" if set_flag else "DROP"
                stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" {kw} NOT NULL', ()))
            elif act == "УСТАНОВИТЬ/СНЯТЬ DEFAULT":
                if not col: raise ValueError("Укажите имя столбца")
                if set_flag and not default: raise ValueError("Укажите DEFAULT-выражение")
                if set_flag:
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" SET DEFAULT {default}', ()))
                else:
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" DROP DEFAULT', ()))
            db.exec_txn(stmts)
            QMessageBox.information(self, "OK", "Изменения применены.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка ALTER TABLE", str(e))