from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QCheckBox)
from PyQt5.QtCore import Qt
import re
import db

_AGG_FUNCS = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
_CMP_OPS_WITH_VALUE = [">=", ">", "=", "<=", "<", "<>", "BETWEEN", "NOT BETWEEN", "IN", "NOT IN"]
_CMP_OPS_NO_VALUE   = ["IS NULL", "IS NOT NULL"]

def _is_number(s: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", s.strip()))

def _sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"

def _id_quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

class SelectBuilderDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("SELECT — конструктор")
        self.setMinimumSize(1920, 1400)

        self.setStyleSheet("""
            QDialog {
                background-color: rgba(16, 30, 41, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-size: 20px;
                padding: 8px;
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
                font-size: 24px;
            }
            QTextEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 10px;
                font-size: 20px;
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
                               font-size: 22px;
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
            QCheckBox {
                color: white;
                padding: 6px;
                font-size: 24px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid rgba(46, 82, 110, 255);
                background-color: rgba(25, 45, 60, 200);
            }
            QCheckBox::indicator:checked {
                background-color: rgba(2, 65, 118, 255);
            }
            QCheckBox::indicator:hover {
                border: 1px solid rgba(66, 122, 160, 255);
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

        # Таблица
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        for s,t in db.list_tables(schema):
            self.cbTable.addItem(f"{s}.{t}", (s,t))
        self.cbTable.currentIndexChanged.connect(self._load_columns)
        hl.addWidget(self.cbTable, 1)
        L.addLayout(hl)

        # Блок SELECT: обычные столбцы
        L.addWidget(QLabel("Столбцы (SELECT — неагрегированные):"))
        self.colsList = QListWidget()
        self.colsList.setSelectionMode(self.colsList.MultiSelection)
        L.addWidget(self.colsList, 2)

        # Блок SELECT: агрегаты
        L.addWidget(QLabel("Агрегаты (SELECT — добавляются отдельными выражениями):"))
        aggRow = QHBoxLayout()
        self.cbSelAggFunc = QComboBox(); self.cbSelAggFunc.addItems(_AGG_FUNCS)
        self.cbSelAggCol  = QComboBox()  # заполняется при смене таблицы
        self.cbSelAggCol.addItem("*")    # для COUNT(*)
        self.cbSelAggDistinct = QCheckBox("DISTINCT")
        self.edSelAggAlias = QLineEdit(); self.edSelAggAlias.setPlaceholderText("Псевдоним (alias), опционально")
        self.btnSelAggAdd = QPushButton("Добавить в SELECT")
        self.btnSelAggDel = QPushButton("Удалить выбранные")
        aggRow.addWidget(QLabel("Функция")); aggRow.addWidget(self.cbSelAggFunc, 1)
        aggRow.addWidget(QLabel("Столбец")); aggRow.addWidget(self.cbSelAggCol, 1)
        aggRow.addWidget(self.cbSelAggDistinct)
        aggRow.addWidget(QLabel("Алиас")); aggRow.addWidget(self.edSelAggAlias, 1)
        aggRow.addWidget(self.btnSelAggAdd); aggRow.addWidget(self.btnSelAggDel)
        L.addLayout(aggRow)

        self.selAggList = QListWidget()
        L.addWidget(self.selAggList, 1)

        # WHERE / GROUP / HAVING / ORDER
        self.edWhere  = QLineEdit(); self.edWhere.setPlaceholderText("WHERE (без слова WHERE)")
        self.edGroup  = QLineEdit(); self.edGroup.setPlaceholderText("GROUP BY (можно оставить пустым — есть авто)")
        self.edHaving = QLineEdit(); self.edHaving.setPlaceholderText("HAVING (сюда пишет конструктор ниже)")
        self.edOrder  = QLineEdit(); self.edOrder.setPlaceholderText("ORDER BY")
        for w in (self.edWhere,self.edGroup,self.edHaving,self.edOrder): L.addWidget(w)

        # Авто-GROUP BY
        self.cbAutoGroup = QCheckBox("Автоматически подставлять GROUP BY по выбранным неагрегированным столбцам (если есть агрегаты или HAVING)")
        self.cbAutoGroup.setChecked(True)
        L.addWidget(self.cbAutoGroup)

        # HAVING — конструктор
        L.addWidget(QLabel("HAVING — конструктор"))
        row1 = QHBoxLayout()
        self.cbHavingFunc = QComboBox(); self.cbHavingFunc.addItems(_AGG_FUNCS)
        self.cbHavingColumn = QComboBox(); self.cbHavingColumn.addItem("*")
        self.cbHavingOp = QComboBox(); self.cbHavingOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
        self.edHavingValue = QLineEdit(); self.edHavingValue.setPlaceholderText("значение (для IN: a,b,c | BETWEEN: a AND b)")
        self.btnHavingAdd = QPushButton("Добавить"); self.btnHavingDel = QPushButton("Удалить выбранные")
        row1.addWidget(QLabel("Функция")); row1.addWidget(self.cbHavingFunc, 1)
        row1.addWidget(QLabel("Столбец")); row1.addWidget(self.cbHavingColumn, 1)
        row1.addWidget(QLabel("Оператор")); row1.addWidget(self.cbHavingOp, 1)
        row1.addWidget(QLabel("Значение")); row1.addWidget(self.edHavingValue, 2)
        row1.addWidget(self.btnHavingAdd); row1.addWidget(self.btnHavingDel)
        L.addLayout(row1)

        self.havingList = QListWidget()
        L.addWidget(self.havingList, 1)

        # SQL / выполнение
        self.btnGenerate = QPushButton("Сгенерировать SQL")
        self.sqlView = QTextEdit()
        self.btnRun = QPushButton("Выполнить и показать")
        L.addWidget(self.btnGenerate); L.addWidget(self.sqlView,1); L.addWidget(self.btnRun)

        self.tbl = QTableWidget(); L.addWidget(self.tbl,4)

        # Сигналы
        self.btnGenerate.clicked.connect(self._gen_sql)
        self.btnRun.clicked.connect(self._run_sql)

        self.btnHavingAdd.clicked.connect(self._add_having)
        self.btnHavingDel.clicked.connect(self._del_having)
        self.cbHavingOp.currentIndexChanged.connect(self._on_having_op_change)

        self.btnSelAggAdd.clicked.connect(self._add_select_agg)
        self.btnSelAggDel.clicked.connect(self._del_select_agg)
        self.cbSelAggFunc.currentIndexChanged.connect(self._on_select_agg_func_change)

        self._load_columns()

    # UI helpers 
    def _on_having_op_change(self):
        op = self.cbHavingOp.currentText()
        self.edHavingValue.setEnabled(op in _CMP_OPS_WITH_VALUE)

    def _on_select_agg_func_change(self):
        func = self.cbSelAggFunc.currentText()
        # Для COUNT разрешаем "*"
        pass

    def _load_columns(self):
        self.colsList.clear()
        self.cbHavingColumn.clear()
        self.cbHavingColumn.addItem("*")
        self.cbSelAggCol.clear()
        self.cbSelAggCol.addItem("*") 

        s,t = self.cbTable.currentData()
        for c in db.list_columns(s,t):
            name = c["column_name"]
            it = QListWidgetItem(name)
            it.setSelected(True)
            self.colsList.addItem(it)

            self.cbHavingColumn.addItem(name)
            self.cbSelAggCol.addItem(name)

    # HAVING builder
    def _add_having(self):
        func = self.cbHavingFunc.currentText().strip()
        col  = self.cbHavingColumn.currentText().strip()
        op   = self.cbHavingOp.currentText().strip()
        val  = self.edHavingValue.text().strip()

        if col == "*" and func != "COUNT":
            QMessageBox.warning(self, "HAVING", "Звёздочка (*) допустима только с COUNT.")
            return

        col_expr = "*" if col == "*" else _id_quote(col)
        expr = f"{func}({col_expr}) {op}"

        if op in _CMP_OPS_WITH_VALUE:
            if op.endswith("IN"):
                if not val:
                    QMessageBox.warning(self, "HAVING", "Для IN укажите список значений (через запятую).")
                    return
                parts = [p.strip() for p in val.split(',') if p.strip()]
                if not parts:
                    QMessageBox.warning(self, "HAVING", "Список для IN пуст.")
                    return
                norm = [p if _is_number(p) else _sql_quote(p) for p in parts]
                expr += " (" + ", ".join(norm) + ")"
            elif op.endswith("BETWEEN"):
                m = re.match(r"(.+)\s+AND\s+(.+)", val, flags=re.I)
                if not m:
                    QMessageBox.warning(self, "HAVING", "Для BETWEEN укажите: a AND b")
                    return
                a, b = m.group(1).strip(), m.group(2).strip()
                a = a if _is_number(a) else _sql_quote(a)
                b = b if _is_number(b) else _sql_quote(b)
                expr += f" {a} AND {b}"
            else:
                if not val:
                    QMessageBox.warning(self, "HAVING", "Укажите значение для сравнения.")
                    return
                v = val if _is_number(val) else _sql_quote(val)
                expr += f" {v}"

        self.havingList.addItem(expr)
        self._sync_having_text()

    def _del_having(self):
        for it in self.havingList.selectedItems():
            row = self.havingList.row(it)
            self.havingList.takeItem(row)
        self._sync_having_text()

    def _sync_having_text(self):
        clauses = [self.havingList.item(i).text() for i in range(self.havingList.count())]
        self.edHaving.setText(" AND ".join(clauses))

    # SELECT aggregates builder
    def _add_select_agg(self):
        func = self.cbSelAggFunc.currentText().strip()
        col  = self.cbSelAggCol.currentText().strip()
        distinct = self.cbSelAggDistinct.isChecked()
        alias = self.edSelAggAlias.text().strip()

        if col == "*" and func != "COUNT":
            QMessageBox.warning(self, "SELECT агрегаты", "Звёздочка (*) допустима только с COUNT.")
            return
        if col == "*" and distinct:
            QMessageBox.warning(self, "SELECT агрегаты", "DISTINCT с * недопустим.")
            return

        col_expr = "*" if col == "*" else _id_quote(col)
        inner = f"DISTINCT {col_expr}" if distinct else col_expr
        expr = f"{func}({inner})"
        if alias:
            expr = f"{expr} AS {_id_quote(alias)}"

        self.selAggList.addItem(expr)
        self.edSelAggAlias.clear()

    def _del_select_agg(self):
        for it in self.selAggList.selectedItems():
            row = self.selAggList.row(it)
            self.selAggList.takeItem(row)

    # SQL generation
    def _gen_sql(self):
        s,t = self.cbTable.currentData()

        # Неагрегированные поля
        nonagg_cols = [i.text() for i in self.colsList.selectedItems()]
        nonagg_sql  = [_id_quote(c) for c in nonagg_cols]

        # Агрегаты из списка
        agg_sql = [self.selAggList.item(i).text() for i in range(self.selAggList.count())]

        # Если вообще ничего не выбрано - ставим *
        select_items = (nonagg_sql + agg_sql) if (nonagg_sql or agg_sql) else ["*"]
        cols_sql = ", ".join(select_items)

        where_txt  = self.edWhere.text().strip()
        group_txt  = self.edGroup.text().strip()
        having_txt = self.edHaving.text().strip()
        order_txt  = self.edOrder.text().strip()

        parts = [f"SELECT {cols_sql} FROM {s}.{t}"]
        if where_txt:
            parts.append("WHERE " + where_txt)

        # Авто-GROUP BY
        has_aggregates = len(agg_sql) > 0
        if self.cbAutoGroup.isChecked():
            need_group = has_aggregates or bool(having_txt)
            if need_group and not group_txt:
                if nonagg_sql:
                    group_txt = ", ".join(nonagg_sql)
                else:
                    group_txt = ""  # только агрегаты

        if group_txt:
            parts.append("GROUP BY " + group_txt)
        if having_txt:
            parts.append("HAVING " + having_txt)
        if order_txt:
            parts.append("ORDER BY " + order_txt)

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
