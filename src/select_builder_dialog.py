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
                font-size: 24px;
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
