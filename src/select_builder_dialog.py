from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
import db

class SelectBuilderDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("SELECT — конструктор")
        self.setMinimumSize(900, 600)

        L = QVBoxLayout(self)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        for s,t in db.list_tables(schema):
            self.cbTable.addItem(f"{s}.{t}", (s,t))
        self.cbTable.currentIndexChanged.connect(self._load_columns)
        hl.addWidget(self.cbTable, 1)
        L.addLayout(hl)

        self.colsList = QListWidget(); self.colsList.setSelectionMode(self.colsList.MultiSelection)
        L.addWidget(QLabel("Столбцы:")); L.addWidget(self.colsList, 2)

        self.edWhere  = QLineEdit(); self.edWhere.setPlaceholderText("WHERE (без слова WHERE)")
        self.edGroup  = QLineEdit(); self.edGroup.setPlaceholderText("GROUP BY")
        self.edHaving = QLineEdit(); self.edHaving.setPlaceholderText("HAVING")
        self.edOrder  = QLineEdit(); self.edOrder.setPlaceholderText("ORDER BY")
        for w in (self.edWhere,self.edGroup,self.edHaving,self.edOrder): L.addWidget(w)

        self.btnGenerate = QPushButton("Сгенерировать SQL")
        self.sqlView = QTextEdit()
        self.btnRun = QPushButton("Выполнить и показать")
        L.addWidget(self.btnGenerate); L.addWidget(self.sqlView,1); L.addWidget(self.btnRun)

        self.tbl = QTableWidget(); L.addWidget(self.tbl,4)

        self.btnGenerate.clicked.connect(self._gen_sql)
        self.btnRun.clicked.connect(self._run_sql)
        self._load_columns()

    def _load_columns(self):
        self.colsList.clear()
        s,t = self.cbTable.currentData()
        for c in db.list_columns(s,t):
            it = QListWidgetItem(c["column_name"]); it.setSelected(True); self.colsList.addItem(it)

    def _gen_sql(self):
        s,t = self.cbTable.currentData()
        cols = [i.text() for i in self.colsList.selectedItems()]
        cols_sql = ", ".join([f'"{c}"' for c in cols]) if cols else "*"
        parts = [f"SELECT {cols_sql} FROM {s}.{t}"]
        if self.edWhere.text().strip():  parts.append("WHERE " + self.edWhere.text().strip())
        if self.edGroup.text().strip():  parts.append("GROUP BY " + self.edGroup.text().strip())
        if self.edHaving.text().strip(): parts.append("HAVING " + self.edHaving.text().strip())
        if self.edOrder.text().strip():  parts.append("ORDER BY " + self.edOrder.text().strip())
        self.sqlView.setPlainText("\n".join(parts))

    def _run_sql(self):
        sql = self.sqlView.toPlainText().strip()
        if not sql.lower().startswith("select"):
            QMessageBox.warning(self, "SELECT", "Разрешён только SELECT")
            return
        try:
            cols, rows = db.preview(sql, limit=500)
            self.tbl.setColumnCount(len(cols)); self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,v in enumerate(row):
                    self.tbl.setItem(r,c, QTableWidgetItem("" if v is None else str(v)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка SELECT", str(e))
