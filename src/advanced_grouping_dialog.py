from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
import db


class AdvancedGroupingDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Advanced Grouping (ROLLUP, CUBE, GROUPING SETS)")
        self.setMinimumSize(1400, 900)

        self.setStyleSheet("""
            QDialog {
                background-color: rgba(16, 30, 41, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-size: 16px;
                padding: 8px;
                font-weight: bold;
            }
            QComboBox {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 12px;
                min-height: 40px;
                font-size: 20px;
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
                font-size: 18px;
                padding: 12px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 8px;
            }
            QTextEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Courier New', monospace;
            }
            QTableWidget {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                gridline-color: rgba(46, 82, 110, 150);
                font-size: 18px;
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
            QHeaderView::section {
                background-color: rgba(2, 65, 118, 255);
                color: white;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
            QListWidget {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                font-size: 18px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(46, 82, 110, 100);
            }
            QListWidget::item:selected {
                background-color: rgba(2, 65, 118, 255);
                color: white;
            }
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 12px;
                min-height: 40px;
                min-width: 120px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 100);
            }
            QRadioButton {
                color: white;
                font-size: 18px;
                padding: 6px;
                font-weight: bold;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid rgba(46, 82, 110, 255);
                background-color: rgba(25, 45, 60, 200);
            }
            QRadioButton::indicator:checked {
                background-color: rgba(2, 65, 118, 255);
                border: 2px solid rgba(2, 65, 118, 255);
            }
            QGroupBox {
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgba(46, 82, 110, 255);
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: rgba(0, 125, 236, 255);
            }
        """)

        L = QVBoxLayout(self)

        # Table selection
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Table:"))
        self.cbTable = QComboBox()
        for s, t in db.list_tables(schema):
            self.cbTable.addItem(f"{s}.{t}", (s, t))
        self.cbTable.currentIndexChanged.connect(self._load_columns)
        h1.addWidget(self.cbTable, 1)
        L.addLayout(h1)

        # Grouping type selection
        groupBox = QGroupBox("Grouping Type")
        groupLayout = QHBoxLayout()
        self.btnGroup = QButtonGroup()

        self.rbSimple = QRadioButton("Simple GROUP BY")
        self.rbRollup = QRadioButton("ROLLUP")
        self.rbCube = QRadioButton("CUBE")
        self.rbGroupingSets = QRadioButton("GROUPING SETS")

        self.rbSimple.setChecked(True)

        self.btnGroup.addButton(self.rbSimple)
        self.btnGroup.addButton(self.rbRollup)
        self.btnGroup.addButton(self.rbCube)
        self.btnGroup.addButton(self.rbGroupingSets)

        groupLayout.addWidget(self.rbSimple)
        groupLayout.addWidget(self.rbRollup)
        groupLayout.addWidget(self.rbCube)
        groupLayout.addWidget(self.rbGroupingSets)
        groupBox.setLayout(groupLayout)
        L.addWidget(groupBox)

        # Columns selection
        L.addWidget(QLabel("Select Grouping Columns (order matters for ROLLUP):"))
        self.colsList = QListWidget()
        self.colsList.setSelectionMode(self.colsList.MultiSelection)
        L.addWidget(self.colsList, 2)

        # For GROUPING SETS - define custom sets
        L.addWidget(QLabel("GROUPING SETS Configuration (comma-separated, e.g., col1,col2):"))
        self.groupingSetsText = QTextEdit()
        self.groupingSetsText.setMaximumHeight(80)
        self.groupingSetsText.setPlaceholderText("Example: col1\ncol2\ncol1,col2")
        L.addWidget(self.groupingSetsText)

        # Aggregate functions
        L.addWidget(QLabel("Aggregate Functions:"))
        aggRow = QHBoxLayout()
        self.cbAggFunc = QComboBox()
        self.cbAggFunc.addItems(["COUNT", "SUM", "AVG", "MIN", "MAX"])
        self.cbAggCol = QComboBox()
        self.cbAggCol.addItem("*")
        self.btnAggAdd = QPushButton("Add Aggregate")
        self.btnAggDel = QPushButton("Delete Selected")
        aggRow.addWidget(QLabel("Function:"))
        aggRow.addWidget(self.cbAggFunc, 1)
        aggRow.addWidget(QLabel("Column:"))
        aggRow.addWidget(self.cbAggCol, 1)
        aggRow.addWidget(self.btnAggAdd)
        aggRow.addWidget(self.btnAggDel)
        L.addLayout(aggRow)

        self.aggList = QListWidget()
        L.addWidget(self.aggList, 1)

        # SQL Preview and Execute
        self.btnGenerate = QPushButton("Generate SQL")
        self.sqlView = QTextEdit()
        self.sqlView.setMaximumHeight(150)
        self.btnRun = QPushButton("Execute Query")
        L.addWidget(self.btnGenerate)
        L.addWidget(self.sqlView)
        L.addWidget(self.btnRun)

        # Results table
        self.tbl = QTableWidget()
        L.addWidget(self.tbl, 4)

        # Connect signals
        self.btnGenerate.clicked.connect(self._generate_sql)
        self.btnRun.clicked.connect(self._run_sql)
        self.btnAggAdd.clicked.connect(self._add_aggregate)
        self.btnAggDel.clicked.connect(self._del_aggregate)
        self.btnGroup.buttonClicked.connect(self._on_grouping_type_changed)

        self._load_columns()

    def _load_columns(self):
        self.colsList.clear()
        self.cbAggCol.clear()
        self.cbAggCol.addItem("*")

        s, t = self.cbTable.currentData()
        if not s or not t:
            return

        for c in db.list_columns(s, t):
            name = c["column_name"]
            item = QListWidgetItem(name)
            self.colsList.addItem(item)
            self.cbAggCol.addItem(name)

    def _on_grouping_type_changed(self):
        is_grouping_sets = self.rbGroupingSets.isChecked()
        self.groupingSetsText.setEnabled(is_grouping_sets)

    def _add_aggregate(self):
        func = self.cbAggFunc.currentText()
        col = self.cbAggCol.currentText()

        if col == "*" and func != "COUNT":
            QMessageBox.warning(self, "Invalid", "Only COUNT can use *")
            return

        col_expr = "*" if col == "*" else f'"{col}"'
        expr = f"{func}({col_expr})"
        self.aggList.addItem(expr)

    def _del_aggregate(self):
        for item in self.aggList.selectedItems():
            row = self.aggList.row(item)
            self.aggList.takeItem(row)

    def _generate_sql(self):
        s, t = self.cbTable.currentData()
        if not s or not t:
            QMessageBox.warning(self, "Error", "Select a table")
            return

        # Get selected grouping columns
        group_cols = [item.text() for item in self.colsList.selectedItems()]

        # Get aggregates
        agg_exprs = [self.aggList.item(i).text() for i in range(self.aggList.count())]

        if not agg_exprs:
            QMessageBox.warning(self, "Error", "Add at least one aggregate function")
            return

        # Build SELECT clause
        select_parts = [f'"{col}"' for col in group_cols] + agg_exprs
        select_clause = ", ".join(select_parts) if select_parts else "*"

        # Build GROUP BY clause based on type
        group_clause = ""

        if self.rbSimple.isChecked():
            if group_cols:
                quoted_cols = [f'"{col}"' for col in group_cols]
                group_clause = f"GROUP BY {', '.join(quoted_cols)}"

        elif self.rbRollup.isChecked():
            if not group_cols:
                QMessageBox.warning(self, "Error", "Select at least one column for ROLLUP")
                return
            quoted_cols = [f'"{col}"' for col in group_cols]
            group_clause = f"GROUP BY ROLLUP({', '.join(quoted_cols)})"

        elif self.rbCube.isChecked():
            if not group_cols:
                QMessageBox.warning(self, "Error", "Select at least one column for CUBE")
                return
            quoted_cols = [f'"{col}"' for col in group_cols]
            group_clause = f"GROUP BY CUBE({', '.join(quoted_cols)})"

        elif self.rbGroupingSets.isChecked():
            sets_text = self.groupingSetsText.toPlainText().strip()
            if not sets_text:
                QMessageBox.warning(self, "Error", "Define GROUPING SETS")
                return

            # Parse grouping sets
            lines = [line.strip() for line in sets_text.split('\n') if line.strip()]
            sets = []
            for line in lines:
                if ',' in line:
                    cols = [f'"{c.strip()}"' for c in line.split(',') if c.strip()]
                    sets.append(f"({', '.join(cols)})")
                else:
                    sets.append(f'"{line}"')

            group_clause = f"GROUP BY GROUPING SETS({', '.join(sets)})"

        # Build full SQL
        sql = f"SELECT {select_clause}\nFROM {s}.{t}"
        if group_clause:
            sql += f"\n{group_clause}"
        sql += "\nORDER BY 1"

        self.sqlView.setPlainText(sql)

    def _run_sql(self):
        sql = self.sqlView.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Error", "Generate SQL first")
            return

        try:
            cols, rows = db.preview(sql, limit=1000)
            self.tbl.setColumnCount(len(cols))
            self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    self.tbl.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))

        except Exception as e:
            QMessageBox.critical(self, "Query Error", str(e))
