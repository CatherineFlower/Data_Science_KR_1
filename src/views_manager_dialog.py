from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit,
    QInputDialog
)
from PyQt5.QtCore import Qt
import db


class ViewsManagerDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Views Manager")
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
        """)

        L = QVBoxLayout(self)

        # Action buttons
        btnRow = QHBoxLayout()
        self.btnCreate = QPushButton("Create New View")
        self.btnRefresh = QPushButton("Refresh List")
        self.btnViewData = QPushButton("View Data")
        self.btnViewDef = QPushButton("View Definition")
        self.btnDrop = QPushButton("Drop View")

        btnRow.addWidget(self.btnCreate)
        btnRow.addWidget(self.btnRefresh)
        btnRow.addWidget(self.btnViewData)
        btnRow.addWidget(self.btnViewDef)
        btnRow.addWidget(self.btnDrop)
        btnRow.addStretch()
        L.addLayout(btnRow)

        # Views list
        L.addWidget(QLabel("Existing Views:"))
        self.viewsList = QListWidget()
        L.addWidget(self.viewsList, 2)

        # SQL/Data display area
        L.addWidget(QLabel("View Definition / Data:"))
        self.displayArea = QTextEdit()
        self.displayArea.setReadOnly(True)
        L.addWidget(self.displayArea, 2)

        # Data table
        self.tbl = QTableWidget()
        L.addWidget(self.tbl, 3)

        # Connect signals
        self.btnCreate.clicked.connect(self._create_view)
        self.btnRefresh.clicked.connect(self._load_views)
        self.btnViewData.clicked.connect(self._view_data)
        self.btnViewDef.clicked.connect(self._view_definition)
        self.btnDrop.clicked.connect(self._drop_view)

        self._load_views()

    def _load_views(self):
        self.viewsList.clear()
        try:
            sql = """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = %s
                ORDER BY table_name
            """
            cols, rows = db.run_select(sql, (self.schema,))
            for row in rows:
                self.viewsList.addItem(row[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load views: {e}")

    def _create_view(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New View")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("View Name:"))
        nameEdit = QLineEdit()
        nameEdit.setPlaceholderText("my_view")
        layout.addWidget(nameEdit)

        layout.addWidget(QLabel("SELECT Query (without CREATE VIEW):"))
        queryEdit = QTextEdit()
        queryEdit.setPlaceholderText("SELECT col1, col2 FROM table WHERE condition")
        layout.addWidget(queryEdit, 1)

        btnLayout = QHBoxLayout()
        btnCreate = QPushButton("Create")
        btnCancel = QPushButton("Cancel")
        btnLayout.addWidget(btnCreate)
        btnLayout.addWidget(btnCancel)
        layout.addLayout(btnLayout)

        btnCancel.clicked.connect(dialog.reject)

        def do_create():
            name = nameEdit.text().strip()
            query = queryEdit.toPlainText().strip()

            if not name:
                QMessageBox.warning(dialog, "Error", "Enter view name")
                return

            if not query:
                QMessageBox.warning(dialog, "Error", "Enter SELECT query")
                return

            try:
                sql = f'CREATE OR REPLACE VIEW {self.schema}."{name}" AS\n{query}'
                db.exec_txn([(sql, ())])
                QMessageBox.information(dialog, "Success", f"View {name} created")
                dialog.accept()
                self._load_views()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to create view: {e}")

        btnCreate.clicked.connect(do_create)
        dialog.exec_()

    def _view_data(self):
        selected = self.viewsList.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a view")
            return

        view_name = selected.text()

        try:
            sql = f'SELECT * FROM {self.schema}."{view_name}"'
            cols, rows = db.preview(sql, limit=1000)

            self.tbl.setColumnCount(len(cols))
            self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    self.tbl.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))

            self.displayArea.setPlainText(f"Showing data from view: {view_name}\nRows: {len(rows)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view data: {e}")

    def _view_definition(self):
        selected = self.viewsList.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a view")
            return

        view_name = selected.text()

        try:
            sql = """
                SELECT view_definition
                FROM information_schema.views
                WHERE table_schema = %s AND table_name = %s
            """
            cols, rows = db.run_select(sql, (self.schema, view_name))

            if rows:
                definition = rows[0][0]
                self.displayArea.setPlainText(f"View: {view_name}\n\n{definition}")
            else:
                self.displayArea.setPlainText("Definition not found")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get definition: {e}")

    def _drop_view(self):
        selected = self.viewsList.currentItem()
        if not selected:
            QMessageBox.warning(self, "Error", "Select a view")
            return

        view_name = selected.text()

        reply = QMessageBox.question(
            self, "Confirm",
            f"Drop view {view_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                sql = f'DROP VIEW IF EXISTS {self.schema}."{view_name}"'
                db.exec_txn([(sql, ())])
                QMessageBox.information(self, "Success", f"View {view_name} dropped")
                self._load_views()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to drop view: {e}")
