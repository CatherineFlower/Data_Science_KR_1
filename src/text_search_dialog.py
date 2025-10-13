from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
import db

OPS = ["LIKE","ILIKE","~","~*","!~","!~*"]

class TextSearchDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Поиск по тексту (LIKE/Regex)")
        self.setMinimumSize(820, 520)

        L = QVBoxLayout(self)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        for s,t in db.list_tables(schema):
            self.cbTable.addItem(f"{s}.{t}", (s,t))
        self.cbTable.currentIndexChanged.connect(self._load_columns)
        hl.addWidget(self.cbTable,1)
        L.addLayout(hl)

        hl2 = QHBoxLayout()
        self.cbColumn = QComboBox(); hl2.addWidget(QLabel("Столбец:")); hl2.addWidget(self.cbColumn,1)
        self.cbOp = QComboBox(); self.cbOp.addItems(OPS); hl2.addWidget(self.cbOp)
        self.edPattern = QLineEdit(); self.edPattern.setPlaceholderText("Шаблон")
        hl2.addWidget(self.edPattern,2)
        self.btnFind = QPushButton("Искать"); hl2.addWidget(self.btnFind)
        L.addLayout(hl2)

        self.tbl = QTableWidget(); L.addWidget(self.tbl,1)
        self.btnFind.clicked.connect(self._do_search)
        self._load_columns()

    def _load_columns(self):
        self.cbColumn.clear()
        s,t = self.cbTable.currentData()
        for c in db.list_columns(s,t):
            self.cbColumn.addItem(c["column_name"])

    def _do_search(self):
        s,t = self.cbTable.currentData()
        col = self.cbColumn.currentText(); op = self.cbOp.currentText()
        pat = self.edPattern.text().strip()
        if not pat:
            QMessageBox.warning(self, "Паттерн", "Укажите шаблон"); return
        sql = f'SELECT * FROM {s}.{t} WHERE "{col}" {op} %s'
        # Подготовка параметра для LIKE/ILIKE
        param = pat
        if op in ("LIKE","ILIKE") and "%" not in param and "_" not in param:
            param = f"%{param}%"
        try:
            cols, rows = db.preview(sql, limit=500, params=(param,))
            self.tbl.setColumnCount(len(cols)); self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,v in enumerate(row):
                    self.tbl.setItem(r,c, QTableWidgetItem("" if v is None else str(v)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", str(e))
