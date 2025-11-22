from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit,
    QCheckBox
)
from PyQt5.QtCore import Qt
import db


class CTEBuilderDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("CTE (Common Table Expressions) Builder")
        self.setMinimumSize(1500, 1000)

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
            QLineEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 10px;
                font-size: 18px;
                min-height: 20px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 1px solid rgba(66, 122, 160, 255);
            }
            QLineEdit::placeholder {
                color: rgba(200, 200, 200, 150);
                font-size: 18px;
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
            QCheckBox {
                color: white;
                font-size: 18px;
                padding: 6px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid rgba(46, 82, 110, 255);
                background-color: rgba(25, 45, 60, 200);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(2, 65, 118, 255);
            }
        """)

        L = QVBoxLayout(self)

        # CTE Management
        L.addWidget(QLabel("Define CTEs (WITH clauses):"))

        cteRow = QHBoxLayout()
        cteRow.addWidget(QLabel("CTE Name:"))
        self.cteNameEdit = QLineEdit()
        self.cteNameEdit.setPlaceholderText("temp_table")
        cteRow.addWidget(self.cteNameEdit, 1)

        self.chkRecursive = QCheckBox("Recursive")
        cteRow.addWidget(self.chkRecursive)

        self.btnAddCTE = QPushButton("Add CTE")
        self.btnEditCTE = QPushButton("Edit Selected")
        self.btnDeleteCTE = QPushButton("Delete Selected")
        cteRow.addWidget(self.btnAddCTE)
        cteRow.addWidget(self.btnEditCTE)
        cteRow.addWidget(self.btnDeleteCTE)
        L.addLayout(cteRow)

        L.addWidget(QLabel("CTE Query (SELECT statement):"))
        self.cteQueryEdit = QTextEdit()
        self.cteQueryEdit.setMaximumHeight(150)
        self.cteQueryEdit.setPlaceholderText("SELECT col1, col2 FROM table WHERE condition")
        L.addWidget(self.cteQueryEdit)

        L.addWidget(QLabel("Defined CTEs:"))
        self.cteList = QListWidget()
        L.addWidget(self.cteList, 2)

        # Main Query
        L.addWidget(QLabel("Main Query (uses CTEs defined above):"))
        self.mainQueryEdit = QTextEdit()
        self.mainQueryEdit.setMaximumHeight(150)
        self.mainQueryEdit.setPlaceholderText("SELECT * FROM temp_table WHERE condition")
        L.addWidget(self.mainQueryEdit)

        # Action buttons
        btnRow = QHBoxLayout()
        self.btnGenerate = QPushButton("Generate Complete SQL")
        self.btnExecute = QPushButton("Execute Query")
        self.btnClear = QPushButton("Clear All")
        btnRow.addWidget(self.btnGenerate)
        btnRow.addWidget(self.btnExecute)
        btnRow.addWidget(self.btnClear)
        btnRow.addStretch()
        L.addLayout(btnRow)

        # Generated SQL display
        L.addWidget(QLabel("Generated SQL:"))
        self.sqlView = QTextEdit()
        self.sqlView.setReadOnly(True)
        self.sqlView.setMaximumHeight(200)
        L.addWidget(self.sqlView)

        # Results table
        L.addWidget(QLabel("Query Results:"))
        self.tbl = QTableWidget()
        L.addWidget(self.tbl, 4)

        # Connect signals
        self.btnAddCTE.clicked.connect(self._add_cte)
        self.btnEditCTE.clicked.connect(self._edit_cte)
        self.btnDeleteCTE.clicked.connect(self._delete_cte)
        self.btnGenerate.clicked.connect(self._generate_sql)
        self.btnExecute.clicked.connect(self._execute_query)
        self.btnClear.clicked.connect(self._clear_all)

        # Store CTEs as dict: {name: (query, is_recursive)}
        self.ctes = {}

    def _add_cte(self):
        name = self.cteNameEdit.text().strip()
        query = self.cteQueryEdit.toPlainText().strip()
        is_recursive = self.chkRecursive.isChecked()

        if not name:
            QMessageBox.warning(self, "Error", "Enter CTE name")
            return

        if not query:
            QMessageBox.warning(self, "Error", "Enter CTE query")
            return

        self.ctes[name] = (query, is_recursive)
        self._refresh_cte_list()

        self.cteNameEdit.clear()
        self.cteQueryEdit.clear()
        self.chkRecursive.setChecked(False)

    def _edit_cte(self):
        selected = self.cteList.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a CTE to edit")
            return

        cte_text = selected.text()
        name = cte_text.split()[0]

        if name in self.ctes:
            query, is_recursive = self.ctes[name]
            self.cteNameEdit.setText(name)
            self.cteQueryEdit.setPlainText(query)
            self.chkRecursive.setChecked(is_recursive)

            del self.ctes[name]
            self._refresh_cte_list()

    def _delete_cte(self):
        selected = self.cteList.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a CTE to delete")
            return

        cte_text = selected.text()
        name = cte_text.split()[0]

        if name in self.ctes:
            del self.ctes[name]
            self._refresh_cte_list()

    def _refresh_cte_list(self):
        self.cteList.clear()
        for name, (query, is_recursive) in self.ctes.items():
            rec_marker = "[RECURSIVE] " if is_recursive else ""
            display = f"{name} {rec_marker}= {query[:60]}..."
            self.cteList.addItem(display)

    def _generate_sql(self):
        if not self.ctes:
            QMessageBox.warning(self, "Error", "Define at least one CTE")
            return

        main_query = self.mainQueryEdit.toPlainText().strip()
        if not main_query:
            QMessageBox.warning(self, "Error", "Enter main query")
            return

        # Build WITH clause
        has_recursive = any(is_rec for _, (_, is_rec) in self.ctes.items())
        with_keyword = "WITH RECURSIVE" if has_recursive else "WITH"

        cte_parts = []
        for name, (query, is_recursive) in self.ctes.items():
            cte_parts.append(f'  {name} AS (\n    {query}\n  )')

        cte_clause = ",\n".join(cte_parts)

        full_sql = f"{with_keyword}\n{cte_clause}\n{main_query}"

        self.sqlView.setPlainText(full_sql)

    def _execute_query(self):
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

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Confirm",
            "Clear all CTEs and queries?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.ctes.clear()
            self._refresh_cte_list()
            self.cteNameEdit.clear()
            self.cteQueryEdit.clear()
            self.mainQueryEdit.clear()
            self.sqlView.clear()
            self.chkRecursive.setChecked(False)
