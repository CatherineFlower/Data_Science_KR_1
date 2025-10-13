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
                       """)

        L = QVBoxLayout(self)

        hl = QHBoxLayout()
        self.cbLeft = QComboBox(); self.cbRight = QComboBox()
        for s,t in db.list_tables(schema):
            self.cbLeft.addItem(f"{s}.{t}", (s,t))
            self.cbRight.addItem(f"{s}.{t}", (s,t))
        self.cbLeft.currentIndexChanged.connect(self._load_cols)
        self.cbRight.currentIndexChanged.connect(self._load_cols)
        hl.addWidget(QLabel("Левая:")); hl.addWidget(self.cbLeft,1)
        hl.addWidget(QLabel("Правая:")); hl.addWidget(self.cbRight,1)
        L.addLayout(hl)

        hl2 = QHBoxLayout()
        self.leftCols = QComboBox(); self.rightCols = QComboBox()
        self.cbType = QComboBox(); self.cbType.addItems(JOIN_TYPES)
        hl2.addWidget(QLabel("Ключ L:")); hl2.addWidget(self.leftCols,1)
        hl2.addWidget(QLabel("Ключ R:")); hl2.addWidget(self.rightCols,1)
        hl2.addWidget(QLabel("Тип:")); hl2.addWidget(self.cbType)
        L.addLayout(hl2)

        L.addWidget(QLabel("Столбцы в результате:"))
        self.colsList = QListWidget(); self.colsList.setSelectionMode(self.colsList.MultiSelection)
        L.addWidget(self.colsList,2)

        self.sqlView = QTextEdit(); self.sqlView.setReadOnly(False)
        self.btnGen = QPushButton("Сгенерировать SQL")
        self.btnRun = QPushButton("Выполнить")
        L.addWidget(self.btnGen); L.addWidget(self.sqlView,1); L.addWidget(self.btnRun)

        self.tbl = QTableWidget(); L.addWidget(self.tbl,3)

        self.btnGen.clicked.connect(self._gen_sql)
        self.btnRun.clicked.connect(self._run_sql)
        self._load_cols()

    def _load_cols(self):
        self.leftCols.clear(); self.rightCols.clear(); self.colsList.clear()
        sl, tl = self.cbLeft.currentData(); sr, tr = self.cbRight.currentData()
        lcols = [c["column_name"] for c in db.list_columns(sl, tl)]
        rcols = [c["column_name"] for c in db.list_columns(sr, tr)]
        for c in lcols: self.leftCols.addItem(c)
        for c in rcols: self.rightCols.addItem(c)
        for c in lcols: self.colsList.addItem(QListWidgetItem(f"{sl}.{tl}.{c}"))
        for c in rcols: self.colsList.addItem(QListWidgetItem(f"{sr}.{tr}.{c}"))

    def _gen_sql(self):
        sl, tl = self.cbLeft.currentData();  sr, tr = self.cbRight.currentData()
        kl = self.leftCols.currentText();    kr = self.rightCols.currentText()
        jtype = self.cbType.currentText()
        items = self.colsList.selectedItems()
        if items:
            sel = []
            for it in items:
                sch, tab, col = it.text().split(".")
                alias = f'{tab}_{col}'
                sel.append(f'{sch}.{tab}."{col}" AS "{alias}"')
            select_sql = ", ".join(sel)
        else:
            select_sql = "*"
        sql = f"""SELECT {select_sql}
FROM {sl}.{tl} L
{jtype} {sr}.{tr} R
  ON L."{kl}" = R."{kr}"
"""
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
