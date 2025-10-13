
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QPushButton, QTextEdit,
                             QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
import db

JOIN_TYPES = ["INNER JOIN(Внутреннее Объединение)","LEFT JOIN(Левое внешнее соединение)","RIGHT JOIN(Правое внешнее соединение)","FULL JOIN(Декартовое соединение)"]

class JoinWizardDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Мастер соединений (JOIN)")
        self.setMinimumSize(1000, 640)

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
                           QTextEdit {
                               background-color: rgba(25, 45, 60, 200);
                               color: white;
                               border: 1px solid rgba(46, 82, 110, 255);
                               border-radius: 4px;
                               padding: 10px;
                               font-size: 13px;
                               font-family: 'Courier New', monospace;
                           }
                           QTextEdit:focus {
                               border: 1px solid rgba(66, 122, 160, 255);
                           }
                           QTableWidget {
                               background-color: rgba(25, 45, 60, 200);
                               color: white;
                               border: 1px solid rgba(46, 82, 110, 255);
                               border-radius: 4px;
                               gridline-color: rgba(46, 82, 110, 150);
                               font-size: 12px;
                           }
                           QTableWidget::item {
                               background-color: transparent;
                               color: white;
                               border-bottom: 1px solid rgba(46, 82, 110, 100);
                               padding: 8px;
                           }
                           QTableWidget::item:selected {
                               background-color: rgba(2, 65, 118, 200);
                               color: white;
                           }
                           QTableWidget::item:hover {
                               background-color: rgba(45, 65, 85, 200);
                           }
                           QHeaderView::section {
                               background-color: rgba(2, 65, 118, 255);
                               color: white;
                               border: none;
                               padding: 8px;
                               font-weight: bold;
                           }
                           QHeaderView::section:hover {
                               background-color: rgba(2, 65, 118, 200);
                           }
                           QHeaderView::section:pressed {
                               background-color: rgba(2, 65, 118, 100);
                           }
                           QListWidget {
                               background-color: rgba(25, 45, 60, 200);
                               color: white;
                               border: 1px solid rgba(46, 82, 110, 255);
                               border-radius: 4px;
                               font-size: 20px;
                           }
                           QListWidget::item {
                               padding: 8px;
                               border-bottom: 1px solid rgba(46, 82, 110, 100);
                           }
                           QListWidget::item:selected {
                               background-color: rgba(2, 65, 118, 255);
                               color: white;
                           }
                           QListWidget::item:hover {
                               background-color: rgba(35, 55, 75, 200);
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
                            QScrollBar:vertical {
                               border: none;
                               background-color: rgba(25, 45, 60, 200);
                               width: 12px;
                               margin: 0px;
                            }
                           QScrollBar::handle:vertical {
                               background-color: rgba(46, 82, 110, 150);
                               border-radius: 6px;
                               min-height: 20px;
                           }
                           QScrollBar::handle:vertical:hover {
                               background-color: rgba(46, 82, 110, 200);
                           }
                           QScrollBar:horizontal {
                               border: none;
                               background-color: rgba(25, 45, 60, 200);
                               height: 12px;
                               margin: 0px;
                           }
                           QScrollBar::handle:horizontal {
                               background-color: rgba(46, 82, 110, 150);
                               border-radius: 6px;
                               min-width: 20px;
                           }
                           QScrollBar::handle:horizontal:hover {
                               background-color: rgba(46, 82, 110, 200);
                           }
                            QTableView {
                                background-color: rgba(25, 45, 60, 200);
                                color: white;
                                gridline-color: rgba(46, 82, 110, 150);
                                selection-background-color: rgba(2, 65, 118, 200);
                                selection-color: white;
                                outline: none;
                            }
                            QTableView::item {
                                background-color: transparent;
                                color: white;
                                border-bottom: 1px solid rgba(46, 82, 110, 100);
                                padding: 8px;
                            }
                            QTableCornerButton::section {
                                background-color: rgba(2, 65, 118, 255);
                                border: none;
                            }
                            QAbstractScrollArea {
                                background-color: rgba(25, 45, 60, 200);
                            }
                       """)

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
