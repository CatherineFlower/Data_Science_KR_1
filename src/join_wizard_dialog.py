
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QPushButton, QTextEdit,
                             QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
import db

JOIN_TYPES = ["INNER JOIN","LEFT JOIN","RIGHT JOIN","FULL JOIN"]

class JoinWizardDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Мастер соединений (JOIN)")
        self.setMinimumSize(1000, 640)

        L = QVBoxLayout(self)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Левая таблица:"))
        self.cbLeft = QComboBox(); self.cbLeft.addItems([t[1] for t in db.list_tables(schema)])
        self.cbLeft.currentIndexChanged.connect(self._reload_pairs)
        h1.addWidget(self.cbLeft,1)
        h1.addWidget(QLabel("Правая таблица:"))
        self.cbRight = QComboBox(); self.cbRight.addItems([t[1] for t in db.list_tables(schema)])
        self.cbRight.currentIndexChanged.connect(self._reload_pairs)
        h1.addWidget(self.cbRight,1)
        h1.addWidget(QLabel("Тип:"))
        self.cbType = QComboBox(); self.cbType.addItems(JOIN_TYPES)
        h1.addWidget(self.cbType)
        L.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Ключ (L = R):"))
        self.cbPairs = QComboBox()
        h2.addWidget(self.cbPairs, 2)
        L.addLayout(h2)

        L.addWidget(QLabel("Столбцы в результате:"))
        self.colsList = QListWidget(); self.colsList.setSelectionMode(self.colsList.MultiSelection)
        L.addWidget(self.colsList,2)

        self.sqlView = QTextEdit(); self.sqlView.setReadOnly(False)
        self.btnGen = QPushButton("Сгенерировать SQL")
        self.btnRun = QPushButton("Выполнить")
        L.addWidget(self.btnGen); L.addWidget(self.sqlView,1); L.addWidget(self.btnRun)

        self.tbl = QTableWidget(); L.addWidget(self.tbl, 3)

        self.btnGen.clicked.connect(self._generate_sql)
        self.btnRun.clicked.connect(self._run_sql)

        self._reload_pairs()

    def _reload_pairs(self):
        lt = self.cbLeft.currentText()
        rt = self.cbRight.currentText()
        pairs = []
        try:
            pairs = db.list_fk_pairs(self.schema, lt, rt)
        except Exception:
            pairs = []
        try:
            left_cols = {c["column_name"]: c for c in db.list_columns(self.schema, lt)}
            right_cols = {c["column_name"]: c for c in db.list_columns(self.schema, rt)}
            for name in sorted(set(left_cols) & set(right_cols)):
                pairs.append((name, name))
        except Exception:
            pass
        seen = set(); uniq = []
        for l, r in pairs:
            key = (l, r)
            if key not in seen:
                seen.add(key); uniq.append(key)
        self.cbPairs.clear()
        for l, r in uniq:
            self.cbPairs.addItem(f'L."{l}" = R."{r}"', (l, r))
        self.btnGen.setEnabled(bool(uniq))
        self.btnRun.setEnabled(True)

        self.colsList.clear()
        try:
            for c in db.list_columns(self.schema, lt):
                item = QListWidgetItem(f'L.{c["column_name"]}'); item.setSelected(True)
                self.colsList.addItem(item)
            for c in db.list_columns(self.schema, rt):
                item = QListWidgetItem(f'R.{c["column_name"]}'); item.setSelected(False)
                self.colsList.addItem(item)
        except Exception:
            pass

    def _generate_sql(self):
        lt = self.cbLeft.currentText()
        rt = self.cbRight.currentText()
        join_type = self.cbType.currentText()
        data = self.cbPairs.currentData()
        if not data:
            QMessageBox.warning(self, "Ключ", "Нет доступных пар для соединения"); return
        kl, kr = data

        sel_cols = []
        for i in range(self.colsList.count()):
            item = self.colsList.item(i)
            if item.isSelected():
                txt = item.text()
                if txt.startswith("L."):
                    sel_cols.append(f'L."{txt[2:]}" AS "L.{txt[2:]}"')
                elif txt.startswith("R."):
                    sel_cols.append(f'R."{txt[2:]}" AS "R.{txt[2:]}"')
        if not sel_cols:
            sel_cols = ['L.*','R.*']

        sql = f'''SELECT {", ".join(sel_cols)}
                FROM {self.schema}."{lt}" L
                {join_type} {self.schema}."{rt}" R
                ON L."{kl}" = R."{kr}"'''
        self.sqlView.setPlainText(sql)

    def _run_sql(self):
        sql = self.sqlView.toPlainText().strip()
        try:
            cols, rows = db.preview(sql, limit=500)
            self.tbl.setColumnCount(len(cols)); self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,v in enumerate(row):
                    self.tbl.setItem(r,c, QTableWidgetItem("" if v is None else str(v)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка JOIN", str(e))
