import traceback
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                             QPushButton, QTextEdit, QMessageBox, QTabWidget, QWidget, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
import db


class ViewsManagerDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Менеджер представлений (Views)")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(parent.styleSheet() if parent else "")  # Наследуем стиль, если возможно

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.setStyleSheet("""
                        QDialog {
                            background-color: rgba(16, 30, 41, 240);
                            color: white;
                        }
                        QLabel {
                            color: white;
                            font-size: 18px;
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
                            font-weight: bold;
                        }
                        QLineEdit:focus {
                            border: 1px solid rgba(66, 122, 160, 255);
                        }
                        /* Стиль для невалидного ввода */
                        QLineEdit:invalid {
                            border: 2px solid rgba(200, 80, 80, 255);
                        }
                        QLineEdit::placeholder {
                            color: rgba(200, 200, 200, 150);
                            font-size: 12px;
                            font-weight: bold;
                        }
                        QTextEdit {
                            background-color: rgba(25, 45, 60, 200);
                            color: white;
                            border: 1px solid rgba(46, 82, 110, 255);
                            border-radius: 4px;
                            padding: 10px;
                            font-size: 18px;
                            font-family: 'Courier New', monospace;
                            font-weight: bold;
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
                            font-size: 22px;
                            font-weight: bold;
                            outline: none;
                        }
                        QTableWidget::item {
                            background-color: transparent;
                            color: white;
                            border-bottom: 1px solid rgba(46, 82, 110, 100);
                            padding: 8px;
                            font-weight: bold;
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
                            font-size: 13px;
                            border-right: 1px solid rgba(46, 82, 110, 255);
                            border-bottom: 1px solid rgba(46, 82, 110, 255);
                        }
                        QHeaderView::section:last {
                            border-right: none;
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
                            font-weight: bold;
                            outline: none;
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
                            font-weight: bold;
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
                            background-color: rgba(2, 65, 110, 255);
                            border: none;
                        }
                        QAbstractScrollArea {
                            background-color: rgba(25, 45, 60, 200);
                        }
                        /* Добавленные стили для вкладок и чекбоксов */
                        QTabWidget::pane {
                            border: 1px solid rgba(46, 82, 110, 255);
                            background-color: rgba(16, 30, 41, 240);
                        }
                        QTabBar::tab {
                            background-color: rgba(25, 45, 60, 200);
                            color: white;
                            padding: 16px 24px;
                            margin-right: 2px;
                            font-size: 18px;
                            font-weight: bold;
                            border: 1px solid rgba(46, 82, 110, 255);
                            border-bottom: none;
                            border-top-left-radius: 4px;
                            border-top-right-radius: 4px;
                        }
                        QTabBar::tab:selected {
                            background-color: rgba(2, 65, 118, 255);
                            border-color: rgba(66, 122, 160, 255);
                        }
                        QTabBar::tab:hover:!selected {
                            background-color: rgba(2, 65, 118, 150);
                        }
                        QCheckBox {
                            color: white;
                            font-size: 13px;
                            spacing: 10px;
                            font-weight: bold;
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
                    """)

        # Таб 1: Обычные View
        self.tab_views = QWidget()
        self._init_views_tab()
        self.tabs.addTab(self.tab_views, "Представления (VIEW)")

        # Таб 2: Materialized View
        self.tab_mat_views = QWidget()
        self._init_mat_views_tab()
        self.tabs.addTab(self.tab_mat_views, "Материализованные (MAT VIEW)")

        # Область результата (общая)
        self.lblResult = QLabel("Результат / DDL:")
        self.layout.addWidget(self.lblResult)

        self.txtResult = QTextEdit()
        self.txtResult.setReadOnly(True)
        self.txtResult.setMaximumHeight(200)
        self.layout.addWidget(self.txtResult)

        self.tblResult = QTableWidget()
        self.layout.addWidget(self.tblResult)

        self.load_lists()

    def _init_views_tab(self):
        layout = QHBoxLayout(self.tab_views)

        self.listViews = QListWidget()
        layout.addWidget(self.listViews, 1)

        btnLayout = QVBoxLayout()
        # --- NEW BUTTON ---
        self.btnCreateNew = QPushButton("➕ Создать новое")
        self.btnCreateNew.setStyleSheet("background-color: #2E7D32; color: white;")
        
        self.btnViewData = QPushButton("Показать данные")
        self.btnViewDDL = QPushButton("Показать структуру (DDL)")
        self.btnViewDrop = QPushButton("Удалить VIEW")

        btnLayout.addWidget(self.btnCreateNew) # Add to layout
        btnLayout.addSpacing(20)
        btnLayout.addWidget(self.btnViewData)
        btnLayout.addWidget(self.btnViewDDL)
        btnLayout.addWidget(self.btnViewDrop)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        self.btnViewData.clicked.connect(lambda: self._show_data(False))
        self.btnViewDDL.clicked.connect(lambda: self._show_ddl(False))
        self.btnViewDrop.clicked.connect(lambda: self._drop_view(False))
        # --- CONNECT NEW BUTTON ---
        self.btnCreateNew.clicked.connect(self._open_builder)

    # Add this helper method to the ViewsManagerDialog class
    def _open_builder(self):
        from select_builder_dialog import SelectBuilderDialog
        dlg = SelectBuilderDialog(self, self.schema)
        dlg.exec_()
        self.load_lists() # Refresh list after closing builder (in case view was created)

    def _init_mat_views_tab(self):
        layout = QHBoxLayout(self.tab_mat_views)

        self.listMatViews = QListWidget()
        layout.addWidget(self.listMatViews, 1)

        btnLayout = QVBoxLayout()
        self.btnMatData = QPushButton("Показать данные")
        self.btnMatDDL = QPushButton("Показать структуру (DDL)")
        self.btnMatRefresh = QPushButton("Обновить данные (REFRESH)")
        self.btnMatDrop = QPushButton("Удалить MAT VIEW")

        btnLayout.addWidget(self.btnMatData)
        btnLayout.addWidget(self.btnMatDDL)
        btnLayout.addWidget(self.btnMatRefresh)
        btnLayout.addWidget(self.btnMatDrop)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        self.btnMatData.clicked.connect(lambda: self._show_data(True))
        self.btnMatDDL.clicked.connect(lambda: self._show_ddl(True))
        self.btnMatRefresh.clicked.connect(self._refresh_mat)
        self.btnMatDrop.clicked.connect(lambda: self._drop_view(True))

    def load_lists(self):
        self.listViews.clear()
        self.listMatViews.clear()
        try:
            views = db.list_views(self.schema)
            for v in views:
                self.listViews.addItem(v)

            mats = db.list_mat_views(self.schema)
            for m in mats:
                self.listMatViews.addItem(m)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки списков: {e}")

    def _get_current(self, is_mat):
        lst = self.listMatViews if is_mat else self.listViews
        item = lst.currentItem()
        if not item:
            QMessageBox.warning(self, "Выбор", "Выберите представление из списка.")
            return None
        return item.text()

    def _show_data(self, is_mat):
        name = self._get_current(is_mat)
        if not name: return
        try:
            sql = f"SELECT * FROM {self.schema}.\"{name}\" LIMIT 100"
            cols, rows = db.run_select(sql)

            self.tblResult.setColumnCount(len(cols))
            self.tblResult.setRowCount(len(rows))
            self.tblResult.setHorizontalHeaderLabels(cols)

            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.tblResult.setItem(r, c, QTableWidgetItem(str(val)))

            self.txtResult.setText(f"Загружено {len(rows)} строк.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _show_ddl(self, is_mat):
        name = self._get_current(is_mat)
        if not name: return
        try:
            ddl = db.get_view_def(self.schema, name, is_mat)
            self.txtResult.setText(ddl)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _refresh_mat(self):
        name = self._get_current(True)
        if not name: return
        try:
            db.refresh_mat_view(self.schema, name)
            QMessageBox.information(self, "Успех", f"Материализованное представление '{name}' обновлено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _drop_view(self, is_mat):
        name = self._get_current(is_mat)
        if not name: return

        type_str = "MATERIALIZED VIEW" if is_mat else "VIEW"
        ret = QMessageBox.question(self, "Удаление", f"Удалить {type_str} '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            try:
                db.drop_view(self.schema, name, is_mat)
                self.load_lists()
                self.txtResult.setText(f"{type_str} '{name}' удалено.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))