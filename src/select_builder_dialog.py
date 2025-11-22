import traceback
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QCheckBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt, QRegExp  # <-- Добавлено
from PyQt5.QtGui import QRegExpValidator  # <-- Добавлено
import re
import db

_AGG_FUNCS = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
_CMP_OPS_WITH_VALUE = [">=", ">", "=", "<=", "<", "<>", "BETWEEN", "NOT BETWEEN", "IN", "NOT IN"]
_CMP_OPS_NO_VALUE = ["IS NULL", "IS NOT NULL"]
# Добавлено для подзапросов (ANY/ALL/EXISTS)
_SUBQUERY_CMP_OPS = [">=", ">", "=", "<=", "<", "<>"]
_QTY = ["ANY", "ALL"]


def _is_number(s: str) -> bool:
    return bool(re.fullmatch(r"-?\\d+(?:\\.\\d+)?", s.strip()))


def _sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _id_quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class SelectBuilderDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        try:
            super().__init__(parent)
            self.schema = schema
            self.setWindowTitle("SELECT — конструктор")
            self.setMinimumSize(1600, 1000)

            # --- Валидаторы ---
            # Для псевдонимов (aliaces). Строго без кавычек и спецсимволов.
            self._alias_validator = QRegExpValidator(QRegExp(r'^[a-zA-Z_][a-zA-Z0-9_]*$'))
            # Для полей, куда вводится SQL-код (WHERE, ORDER BY)
            # Запрещаем точку с запятой для защиты от простых инъекций.
            self._sql_fragment_validator = QRegExpValidator(QRegExp(r'^[^"\'/\\|`=?!~+<>:;-]*$'))
            # ------------------

            self.setStyleSheet("""
                QDialog {
                    background-color: rgba(16, 30, 41, 240);
                    color: white;
                }
                QLabel {
                    color: white;
                    font-size: 13px;
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
                    font-size: 13px;
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
                    font-size: 13px;
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

            main_layout = QVBoxLayout(self)
            tabs = QTabWidget()
            main_layout.addWidget(tabs)

            # ---------- Страница 1: Основное ----------
            page_main = QWidget()
            L1 = QVBoxLayout(page_main)

            hl = QHBoxLayout()
            hl.addWidget(QLabel("Таблица:"))
            self.cbTable = QComboBox()
            try:
                tables = list(db.list_tables(schema))
            except Exception as e:
                print("Ошибка при получении списка таблиц из db.list_tables:", e)
                tables = []
            for s, t in tables:
                self.cbTable.addItem(f"{s}.{t}", (s, t))
            self.cbTable.currentIndexChanged.connect(self._load_columns)
            hl.addWidget(self.cbTable, 1)
            L1.addLayout(hl)

            L1.addWidget(QLabel("Столбцы (SELECT — неагрегированные):"))
            self.colsList = QListWidget()
            self.colsList.setSelectionMode(self.colsList.MultiSelection)
            L1.addWidget(self.colsList, 2)

            L1.addWidget(QLabel("Агрегаты (SELECT — добавляются отдельными выражениями):"))
            aggRow = QHBoxLayout()
            self.cbSelAggFunc = QComboBox()
            self.cbSelAggFunc.addItems(_AGG_FUNCS)
            self.cbSelAggCol = QComboBox()
            self.cbSelAggCol.addItem("*")
            self.cbSelAggDistinct = QCheckBox("DISTINCT")
            self.edSelAggAlias = QLineEdit()
            self.edSelAggAlias.setPlaceholderText("Псевдоним (alias), опционально")
            self.edSelAggAlias.setValidator(self._alias_validator)  # <-- Валидация
            self.btnSelAggAdd = QPushButton("Добавить в SELECT")
            self.btnSelAggDel = QPushButton("Удалить выбранные")
            for w in [
                QLabel("Функция"), self.cbSelAggFunc, QLabel("Столбец"), self.cbSelAggCol,
                self.cbSelAggDistinct, QLabel("Алиас"), self.edSelAggAlias,
                self.btnSelAggAdd, self.btnSelAggDel
            ]:
                aggRow.addWidget(w)
            L1.addLayout(aggRow)
            self.selAggList = QListWidget()
            L1.addWidget(self.selAggList, 1)

            tabs.addTab(page_main, "Основное")

            # ---------- Страница 2: Фильтры ----------
            page_filters = QWidget()
            L2 = QVBoxLayout(page_filters)

            self.edWhere = QLineEdit()
            self.edWhere.setPlaceholderText("WHERE (без слова WHERE)")
            self.edWhere.setValidator(self._sql_fragment_validator)  # <-- Валидация
            self.edGroup = QLineEdit()
            self.edGroup.setPlaceholderText("GROUP BY (можно оставить пустым — есть авто)")
            self.edGroup.setValidator(self._sql_fragment_validator)  # <-- Валидация
            self.edHaving = QLineEdit()
            self.edHaving.setPlaceholderText("HAVING (сюда пишет конструктор ниже)")
            self.edHaving.setValidator(self._sql_fragment_validator)  # <-- Валидация
            self.edOrder = QLineEdit()
            self.edOrder.setPlaceholderText("ORDER BY")
            self.edOrder.setValidator(self._sql_fragment_validator)  # <-- Валидация

            for w in (self.edWhere, self.edGroup, self.edHaving, self.edOrder):
                L2.addWidget(w)

            self.cbAutoGroup = QCheckBox("Автоматически подставлять GROUP BY по выбранным неагрегированным столбцам")
            self.cbAutoGroup.setChecked(True)
            L2.addWidget(self.cbAutoGroup)
            # === HAVING — конструктор ===
            L2.addWidget(QLabel("HAVING — конструктор"))
            row1 = QHBoxLayout()
            self.cbHavingFunc = QComboBox()
            self.cbHavingFunc.addItems(_AGG_FUNCS)
            self.cbHavingColumn = QComboBox()
            self.cbHavingColumn.addItem("*")
            self.cbHavingOp = QComboBox()
            self.cbHavingOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
            self.edHavingValue = QLineEdit()
            self.edHavingValue.setPlaceholderText("значение (для IN: a,b,c | BETWEEN: a AND b)")
            self.edHavingValue.setValidator(self._sql_fragment_validator)
            # Валидация не нужна, т.к. _sql_quote() корректно обработает кавычки
            self.btnHavingAdd = QPushButton("Добавить")
            self.btnHavingDel = QPushButton("Удалить выбранные")
            for w in [QLabel("Функция"), self.cbHavingFunc, QLabel("Столбец"), self.cbHavingColumn,
                      QLabel("Оператор"), self.cbHavingOp, QLabel("Значение"), self.edHavingValue,
                      self.btnHavingAdd, self.btnHavingDel]:
                row1.addWidget(w)
            L2.addLayout(row1)
            self.havingList = QListWidget()
            L2.addWidget(self.havingList, 1)

            tabs.addTab(page_filters, "Фильтры")

            # ---------- Новая вкладка: Подзапросы ----------
            page_subq = QWidget()
            Lsub = QVBoxLayout(page_subq)

            Lsub.addWidget(QLabel("WHERE — подзапросы (ANY/ALL/EXISTS)"))

            row_sub_top = QHBoxLayout()
            self.cbSubKind = QComboBox()
            self.cbSubKind.addItems(["EXISTS", "NOT EXISTS", "Сравнение с ANY/ALL"])
            self.cbLeftCol = QComboBox()
            self.cbCmpOp = QComboBox()
            self.cbCmpOp.addItems(_SUBQUERY_CMP_OPS)
            self.cbQuantifier = QComboBox()
            self.cbQuantifier.addItems(_QTY)
            row_sub_top.addWidget(QLabel("Тип"))
            row_sub_top.addWidget(self.cbSubKind)
            row_sub_top.addWidget(QLabel("Внешний столбец"))
            row_sub_top.addWidget(self.cbLeftCol, 1)
            row_sub_top.addWidget(QLabel("Оператор"))
            row_sub_top.addWidget(self.cbCmpOp)
            row_sub_top.addWidget(QLabel("Квантор"))
            row_sub_top.addWidget(self.cbQuantifier)
            Lsub.addLayout(row_sub_top)

            row_sub_mid = QHBoxLayout()
            self.cbInnerTable = QComboBox()
            try:
                for s, t in db.list_tables(self.schema):
                    self.cbInnerTable.addItem(f"{s}.{t}", (s, t))
            except Exception as e:
                print("Ошибка при получении списка таблиц для подзапроса:", e)
            self.cbInnerTable.currentIndexChanged.connect(self._load_inner_columns)
            self.cbInnerCol = QComboBox()
            row_sub_mid.addWidget(QLabel("Подзапрос: таблица"))
            row_sub_mid.addWidget(self.cbInnerTable, 1)
            row_sub_mid.addWidget(QLabel("Столбец в подзапросе"))
            row_sub_mid.addWidget(self.cbInnerCol, 1)
            Lsub.addLayout(row_sub_mid)

            row_corr = QHBoxLayout()
            self.cbCorrOuter = QComboBox()
            self.cbCorrInner = QComboBox()
            self.btnCorrAdd = QPushButton("Добавить связь")
            self.btnCorrDel = QPushButton("Удалить связь")
            self.btnCorrSuggest = QPushButton("Подсказать по FK")
            row_corr.addWidget(QLabel("Связь: внешний"))
            row_corr.addWidget(self.cbCorrOuter, 1)
            row_corr.addWidget(QLabel("="))
            row_corr.addWidget(self.cbCorrInner, 1)
            row_corr.addWidget(self.btnCorrAdd)
            row_corr.addWidget(self.btnCorrDel)
            row_corr.addWidget(self.btnCorrSuggest)
            Lsub.addLayout(row_corr)
            self.corrList = QListWidget()
            Lsub.addWidget(self.corrList, 1)

            row_in_where = QHBoxLayout()
            self.cbInWhereCol = QComboBox()
            self.cbInWhereOp = QComboBox()
            self.cbInWhereOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
            self.edInWhereVal = QLineEdit()
            self.edInWhereVal.setPlaceholderText("значение (для IN: a,b,c | BETWEEN: a AND b)")
            self.edInWhereVal.setValidator(self._sql_fragment_validator)
            self.btnInWhereAdd = QPushButton("Добавить условие")
            self.btnInWhereDel = QPushButton("Удалить выбранные")
            row_in_where.addWidget(QLabel("Где (в подзапросе): столбец"))
            row_in_where.addWidget(self.cbInWhereCol, 1)
            row_in_where.addWidget(QLabel("Оператор"))
            row_in_where.addWidget(self.cbInWhereOp)
            row_in_where.addWidget(QLabel("Значение"))
            row_in_where.addWidget(self.edInWhereVal, 1)
            row_in_where.addWidget(self.btnInWhereAdd)
            row_in_where.addWidget(self.btnInWhereDel)
            Lsub.addLayout(row_in_where)
            self.inWhereList = QListWidget()
            Lsub.addWidget(self.inWhereList, 1)

            ctl_row = QHBoxLayout()
            self.btnSubAdd = QPushButton("Добавить фильтр в WHERE");
            self.btnSubDel = QPushButton("Удалить выбранные фильтры")
            ctl_row.addWidget(self.btnSubAdd)
            ctl_row.addWidget(self.btnSubDel)
            Lsub.addLayout(ctl_row)
            self.subFilterList = QListWidget()
            Lsub.addWidget(self.subFilterList, 1)

            tabs.addTab(page_subq, "Подзапросы")

            # ---------- Новая вкладка: Выражения (CASE / COALESCE / NULLIF) ----------
            page_expr = QWidget()
            Lex = QVBoxLayout(page_expr)

            # Заголовок CASE
            row_case_header = QHBoxLayout()
            self.edCaseAlias = QLineEdit()
            self.edCaseAlias.setPlaceholderText("Алиас результирующего столбца")
            self.edCaseAlias.setValidator(self._alias_validator)  # <-- Валидация
            row_case_header.addWidget(QLabel("Алиас"))
            row_case_header.addWidget(self.edCaseAlias, 1)
            Lex.addLayout(row_case_header)

            # WHEN ... THEN ...
            row_when = QHBoxLayout()
            self.cbWhenCol = QComboBox()
            self.cbWhenOp = QComboBox()
            self.cbWhenOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
            self.edWhenVal = QLineEdit()
            self.edWhenVal.setPlaceholderText("значение (IN: a,b,c | BETWEEN: a AND b)")
            self.edWhenVal.setValidator(self._sql_fragment_validator)
            self.edThenVal = QLineEdit()
            self.edThenVal.setPlaceholderText("THEN значение")
            self.edThenVal.setValidator(self._sql_fragment_validator)
            self.btnWhenAdd = QPushButton("Добавить WHEN-THEN")
            self.btnWhenDel = QPushButton("Удалить выбранные")
            for w in [QLabel("WHEN: столбец"), self.cbWhenCol, QLabel("оператор"), self.cbWhenOp,
                      QLabel("значение"), self.edWhenVal, QLabel("THEN"), self.edThenVal,
                      self.btnWhenAdd, self.btnWhenDel]:
                row_when.addWidget(w)
            Lex.addLayout(row_when)
            self.caseWhenList = QListWidget()
            Lex.addWidget(self.caseWhenList, 1)

            # ELSE
            row_else = QHBoxLayout()
            self.edElseVal = QLineEdit()
            self.edElseVal.setPlaceholderText("ELSE значение (опционально)")
            self.edElseVal.setValidator(self._sql_fragment_validator)
            row_else.addWidget(QLabel("ELSE"))
            row_else.addWidget(self.edElseVal, 1)
            Lex.addLayout(row_else)

            # Кнопка "Добавить CASE"
            row_case_ctl = QHBoxLayout()
            self.btnCaseAddExpr = QPushButton("Добавить CASE в SELECT")
            row_case_ctl.addWidget(self.btnCaseAddExpr)
            Lex.addLayout(row_case_ctl)

            # NULL-обработка
            Lex.addWidget(QLabel("NULL-обработка: COALESCE / NULLIF"))

            # COALESCE(col, value)
            row_coalesce = QHBoxLayout()
            self.cbCoalCol = QComboBox()
            self.edCoalVal = QLineEdit()
            self.edCoalVal.setPlaceholderText("подстановка вместо NULL")
            self.edCoalVal.setValidator(self._sql_fragment_validator)
            self.btnCoalesceAdd = QPushButton("Добавить COALESCE(col, value)")
            for w in [QLabel("COALESCE: столбец"), self.cbCoalCol, QLabel(", значение"), self.edCoalVal,
                      self.btnCoalesceAdd]:
                row_coalesce.addWidget(w)
            Lex.addLayout(row_coalesce)

            # NULLIF(col, value)
            row_nullif = QHBoxLayout()
            self.cbNullifCol = QComboBox()
            self.edNullifVal = QLineEdit()
            self.edNullifVal.setPlaceholderText("значение для сравнения")
            self.edNullifVal.setValidator(self._sql_fragment_validator)
            self.btnNullifAdd = QPushButton("Добавить NULLIF(col, value)")
            for w in [QLabel("NULLIF: столбец"), self.cbNullifCol, QLabel(", значение"), self.edNullifVal,
                      self.btnNullifAdd]:
                row_nullif.addWidget(w)
            Lex.addLayout(row_nullif)

            # Итоговый список выражений для SELECT
            Lex.addWidget(QLabel("Выражения для SELECT"))
            self.exprList = QListWidget()
            Lex.addWidget(self.exprList, 1)
            row_expr_ctl = QHBoxLayout()
            self.btnExprDel = QPushButton("Удалить выбранные выражения")
            row_expr_ctl.addWidget(self.btnExprDel)
            Lex.addLayout(row_expr_ctl)

            tabs.addTab(page_expr, "Выражения")

            # ---------- Страница 3: Результат ----------
            page_result = QWidget()
            L3 = QVBoxLayout(page_result)

            self.btnGenerate = QPushButton("Сгенерировать SQL")
            self.sqlView = QTextEdit()
            self.btnRun = QPushButton("Выполнить и показать")
            L3.addWidget(self.btnGenerate)
            L3.addWidget(self.sqlView, 1)
            L3.addWidget(self.btnRun)

            self.tbl = QTableWidget()
            L3.addWidget(self.tbl, 4)

            tabs.addTab(page_result, "Результат")

            # ... (вся остальная часть файла, включая все методы, не изменилась) ...

            # Сигналы и инициализация (подключаем после создания виджетов)
            self.btnGenerate.clicked.connect(self._gen_sql)
            self.btnRun.clicked.connect(self._run_sql)

            # Сигналы и инициализация (подключаем после создания виджетов)
            self.btnGenerate.clicked.connect(self._gen_sql)
            self.btnRun.clicked.connect(self._run_sql)

            # CASE / COALESCE / NULLIF
            self.btnWhenAdd.clicked.connect(self._add_case_when)
            self.btnWhenDel.clicked.connect(self._del_case_when)
            self.cbWhenOp.currentIndexChanged.connect(self._on_when_op_change)
            self.btnCaseAddExpr.clicked.connect(self._add_case_expr)
            self.btnCoalesceAdd.clicked.connect(self._add_coalesce_expr)
            self.btnNullifAdd.clicked.connect(self._add_nullif_expr)
            self.btnExprDel.clicked.connect(self._del_expr)

            # HAVING
            self.btnHavingAdd.clicked.connect(self._add_having)
            self.btnHavingDel.clicked.connect(self._del_having)
            self.cbHavingOp.currentIndexChanged.connect(self._on_having_op_change)

            # SELECT агрегаты
            self.btnSelAggAdd.clicked.connect(self._add_select_agg)
            self.btnSelAggDel.clicked.connect(self._del_select_agg)
            self.cbSelAggFunc.currentIndexChanged.connect(self._on_select_agg_func_change)

            # Подзапросы — события
            self.cbSubKind.currentIndexChanged.connect(self._toggle_sub_ui)
            self.btnCorrAdd.clicked.connect(self._add_corr)
            self.btnCorrDel.clicked.connect(self._del_corr)
            self.btnCorrSuggest.clicked.connect(self._suggest_corr)
            self.btnInWhereAdd.clicked.connect(self._add_in_where)
            self.btnInWhereDel.clicked.connect(self._del_in_where)
            self.btnSubAdd.clicked.connect(self._add_subfilter)
            self.btnSubDel.clicked.connect(self._del_subfilter)
            self.cbInWhereOp.currentIndexChanged.connect(self._on_in_where_op_change)

            # Загрузим колонки и внутренние колонки — безопасно
            self._load_columns()
            self._load_inner_columns()
            self._toggle_sub_ui()

            for lst in (self.colsList, self.selAggList, self.havingList, self.corrList, self.inWhereList,
                        self.subFilterList):
                lst.setFocusPolicy(Qt.NoFocus)

        except Exception as e:
            print("Unhandled exception in SelectBuilderDialog.__init__:", e)
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при инициализации окна:\n{e}")

    # === UI helpers ===
    def _on_having_op_change(self):
        op = self.cbHavingOp.currentText()
        self.edHavingValue.setEnabled(op in _CMP_OPS_WITH_VALUE)

    def _on_in_where_op_change(self):
        op = self.cbInWhereOp.currentText()
        self.edInWhereVal.setEnabled(op in _CMP_OPS_WITH_VALUE)

    def _on_select_agg_func_change(self):
        pass

    def _load_columns(self):
        try:
            self.colsList.clear()
            self.cbHavingColumn.clear()
            self.cbHavingColumn.addItem("*")
            self.cbSelAggCol.clear()
            self.cbSelAggCol.addItem("*")
            # для подзапросов
            self.cbLeftCol.clear()
            self.cbCorrOuter.clear()
            # для выражений
            self.cbWhenCol.clear()
            self.cbCoalCol.clear()
            self.cbNullifCol.clear()

            s, t = self.cbTable.currentData() or (None, None)
            if s is None:
                return
            for c in db.list_columns(s, t):
                name = c["column_name"]
                it = QListWidgetItem(name)
                it.setSelected(True)
                self.colsList.addItem(it)
                self.cbHavingColumn.addItem(name)
                self.cbSelAggCol.addItem(name)
                self.cbLeftCol.addItem(name)
                self.cbCorrOuter.addItem(name)
                # источники для вкладки "Выражения"
                self.cbWhenCol.addItem(name)
                self.cbCoalCol.addItem(name)
                self.cbNullifCol.addItem(name)
        except Exception as e:
            print("Ошибка в _load_columns:", e)
            traceback.print_exc()

    def _load_inner_columns(self):
        try:
            self.cbInnerCol.clear()
            self.cbInWhereCol.clear()
            self.cbCorrInner.clear()
            if self.cbInnerTable.count():
                s2, t2 = self.cbInnerTable.currentData()
            else:
                s2, t2 = self.schema, ""
            if not t2:
                return
            for c in db.list_columns(s2, t2):
                name = c["column_name"]
                self.cbInnerCol.addItem(name)
                self.cbInWhereCol.addItem(name)
                self.cbCorrInner.addItem(name)
        except Exception as e:
            print("Ошибка в _load_inner_columns:", e)
            traceback.print_exc()

    def _toggle_sub_ui(self):
        try:
            kind = self.cbSubKind.currentText()
            any_all = (kind == "Сравнение с ANY/ALL")
            for w in (self.cbLeftCol, self.cbCmpOp, self.cbQuantifier, self.cbInnerCol):
                w.setEnabled(any_all)
        except Exception as e:
            print("Ошибка в _toggle_sub_ui:", e)

    # === Вкладка "Выражения" — CASE/COALESCE/NULLIF ===
    def _on_when_op_change(self):
        op = self.cbWhenOp.currentText()
        self.edWhenVal.setEnabled(op in _CMP_OPS_WITH_VALUE)

    def _add_case_when(self):
        try:
            col = self.cbWhenCol.currentText().strip()
            op = self.cbWhenOp.currentText().strip()
            wval = self.edWhenVal.text().strip()
            tval = self.edThenVal.text().strip()
            if not tval:
                QMessageBox.warning(self, "CASE", "Укажите значение для THEN.")
                return
            when_sql = "WHEN "
            if op in _CMP_OPS_WITH_VALUE:
                if op.endswith("IN"):
                    parts = [p.strip() for p in (wval or "").split(',') if p.strip()]
                    if not parts:
                        QMessageBox.warning(self, "CASE", "Для IN укажите список значений.")
                        return
                    norm = [p if _is_number(p) else _sql_quote(p) for p in parts]
                    cond = f"{_id_quote(col)} IN (" + ", ".join(norm) + ")"
                elif op.endswith("BETWEEN"):
                    m = re.match(r"(.+)\\s+AND\\s+(.+)", wval or "", flags=re.I)
                    if not m:
                        QMessageBox.warning(self, "CASE", "Для BETWEEN укажите: a AND b")
                        return
                    a, b = m.group(1).strip(), m.group(2).strip()
                    a = a if _is_number(a) else _sql_quote(a)
                    b = b if _is_number(b) else _sql_quote(b)
                    cond = f"{_id_quote(col)} BETWEEN {a} AND {b}"
                else:
                    if not wval:
                        QMessageBox.warning(self, "CASE", "Укажите значение для сравнения.")
                        return
                    v = wval if _is_number(wval) else _sql_quote(wval)
                    cond = f"{_id_quote(col)} {op} {v}"
            else:
                cond = f"{_id_quote(col)} {op}"
            when_sql += cond
            tv = tval if _is_number(tval) else _sql_quote(tval)
            when_sql += f" THEN {tv}"
            self.caseWhenList.addItem(when_sql)
            self.edThenVal.clear();
            self.edWhenVal.clear()
        except Exception as e:
            print("Ошибка _add_case_when:", e)

    def _del_case_when(self):
        for it in self.caseWhenList.selectedItems():
            self.caseWhenList.takeItem(self.caseWhenList.row(it))

    def _build_case_sql(self) -> str:
        alias = self.edCaseAlias.text().strip()
        parts = ["CASE"]
        for i in range(self.caseWhenList.count()):
            parts.append(self.caseWhenList.item(i).text())
        else_val = self.edElseVal.text().strip()
        if else_val:
            ev = else_val if _is_number(else_val) else _sql_quote(else_val)
            parts.append(f"ELSE {ev}")
        parts.append("END")
        expr = " ".join(parts)
        if alias:
            expr += f" AS {_id_quote(alias)}"
        return expr

    def _add_case_expr(self):
        try:
            if self.caseWhenList.count() == 0:
                QMessageBox.warning(self, "CASE", "Добавьте хотя бы одну пару WHEN-THEN.")
                return
            expr = self._build_case_sql()
            self.exprList.addItem(expr)
        except Exception as e:
            QMessageBox.critical(self, "CASE", str(e))

    def _add_coalesce_expr(self):
        col = self.cbCoalCol.currentText().strip()
        val = (self.edCoalVal.text() or "").strip()
        if not col or not val:
            QMessageBox.warning(self, "COALESCE", "Укажите столбец и подстановку.")
            return
        v = val if _is_number(val) else _sql_quote(val)
        self.exprList.addItem(f"COALESCE({_id_quote(col)}, {v})")
        self.edCoalVal.clear()

    def _add_nullif_expr(self):
        col = self.cbNullifCol.currentText().strip()
        val = (self.edNullifVal.text() or "").strip()
        if not col or not val:
            QMessageBox.warning(self, "NULLIF", "Укажите столбец и значение для сравнения.")
            return
        v = val if _is_number(val) else _sql_quote(val)
        self.exprList.addItem(f"NULLIF({_id_quote(col)}, {v})")
        self.edNullifVal.clear()

    def _del_expr(self):
        for it in self.exprList.selectedItems():
            self.exprList.takeItem(self.exprList.row(it))

    # === HAVING builder ===
    def _add_having(self):
        try:
            func = self.cbHavingFunc.currentText().strip()
            col = self.cbHavingColumn.currentText().strip()
            op = self.cbHavingOp.currentText().strip()
            val = self.edHavingValue.text().strip()

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
                    m = re.match(r"(.+)\\s+AND\\s+(.+)", val, flags=re.I)
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
        except Exception as e:
            print("Ошибка в _add_having:", e)
            traceback.print_exc()

    def _del_having(self):
        for it in self.havingList.selectedItems():
            row = self.havingList.row(it)
            self.havingList.takeItem(row)
        self._sync_having_text()

    def _sync_having_text(self):
        clauses = [self.havingList.item(i).text() for i in range(self.havingList.count())]
        self.edHaving.setText(" AND ".join(clauses))

    # === Подзапросы (ANY/ALL/EXISTS) ===
    def _add_corr(self):
        outer_col = self.cbCorrOuter.currentText().strip()
        inner_col = self.cbCorrInner.currentText().strip()
        if not outer_col or not inner_col:
            return
        self.corrList.addItem(f"{_id_quote(outer_col)} = sq.{_id_quote(inner_col)}")

    def _del_corr(self):
        for it in self.corrList.selectedItems():
            self.corrList.takeItem(self.corrList.row(it))

    def _suggest_corr(self):
        try:
            s1, t1 = self.cbTable.currentData()
            s2, t2 = self.cbInnerTable.currentData()
            pairs = db.list_fk_pairs(self.schema, t1, t2)
            if not pairs:
                QMessageBox.information(self, "Связи", "FK-отношения между таблицами не найдены.")
                return
            for left_col, right_col in pairs:
                self.corrList.addItem(f"{_id_quote(left_col)} = sq.{_id_quote(right_col)}")
        except Exception as e:
            QMessageBox.warning(self, "Связи", f"Не удалось получить связи: {e}")

    def _add_in_where(self):
        col = self.cbInWhereCol.currentText().strip()
        op = self.cbInWhereOp.currentText().strip()
        val = self.edInWhereVal.text().strip()
        expr = f"sq.{_id_quote(col)} {op}"
        if op in _CMP_OPS_WITH_VALUE:
            if op.endswith("IN"):
                if not val:
                    QMessageBox.warning(self, "Подзапрос: WHERE", "Для IN укажите список значений (a,b,c)")
                    return
                parts = [p.strip() for p in val.split(',') if p.strip()]
                norm = [p if _is_number(p) else _sql_quote(p) for p in parts]
                expr += " (" + ", ".join(norm) + ")"
            elif op.endswith("BETWEEN"):
                m = re.match(r"(.+)\\s+AND\\s+(.+)", val, flags=re.I)
                if not m:
                    QMessageBox.warning(self, "Подзапрос: WHERE", "Для BETWEEN укажите: a AND b")
                    return
                a, b = m.group(1).strip(), m.group(2).strip()
                a = a if _is_number(a) else _sql_quote(a)
                b = b if _is_number(b) else _sql_quote(b)
                expr += f" {a} AND {b}"
            else:
                if not val:
                    QMessageBox.warning(self, "Подзапрос: WHERE", "Укажите значение для сравнения")
                    return
                v = val if _is_number(val) else _sql_quote(val)
                expr += f" {v}"
        self.inWhereList.addItem(expr)

    def _del_in_where(self):
        for it in self.inWhereList.selectedItems():
            self.inWhereList.takeItem(self.inWhereList.row(it))

    def _build_subquery_sql(self) -> str:
        kind = self.cbSubKind.currentText()
        s2, t2 = self.cbInnerTable.currentData()
        inner_from = f"{s2}.{t2}"
        corr = [self.corrList.item(i).text() for i in range(self.corrList.count())]
        inwhere = [self.inWhereList.item(i).text() for i in range(self.inWhereList.count())]
        where_parts = []
        if corr:
            where_parts.append(" AND ".join(corr))
        if inwhere:
            where_parts.append(" AND ".join(inwhere))
        inner_where = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        if kind in ("EXISTS", "NOT EXISTS"):
            return f"{kind} (SELECT 1 FROM {inner_from} AS sq{inner_where})"
        left_col = self.cbLeftCol.currentText().strip()
        op = self.cbCmpOp.currentText().strip()
        qty = self.cbQuantifier.currentText().strip()
        inner_col = self.cbInnerCol.currentText().strip()
        sub = f"SELECT {_id_quote(inner_col)} FROM {inner_from} AS sq{inner_where}"
        return f"{_id_quote(left_col)} {op} {qty} ({sub})"

    def _add_subfilter(self):
        try:
            expr = self._build_subquery_sql()
            self.subFilterList.addItem(expr)
        except Exception as e:
            QMessageBox.critical(self, "Подзапрос", str(e))

    def _del_subfilter(self):
        for it in self.subFilterList.selectedItems():
            self.subFilterList.takeItem(self.subFilterList.row(it))

    def subFilterStrings(self):
        return [self.subFilterList.item(i).text() for i in range(self.subFilterList.count())]

    def _add_select_agg(self):
        try:
            func = self.cbSelAggFunc.currentText().strip()
            col = self.cbSelAggCol.currentText().strip()
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
        except Exception as e:
            print("Ошибка в _add_select_agg:", e)
            traceback.print_exc()

    def _del_select_agg(self):
        for it in self.selAggList.selectedItems():
            row = self.selAggList.row(it)
            self.selAggList.takeItem(row)

    def _gen_sql(self):
        try:
            s, t = self.cbTable.currentData() or (None, None)
            if s is None:
                QMessageBox.warning(self, "SELECT", "Выберите таблицу.")
                return

            nonagg_cols = [i.text() for i in self.colsList.selectedItems()]
            nonagg_sql = [_id_quote(c) for c in nonagg_cols]

            agg_sql = [self.selAggList.item(i).text() for i in range(self.selAggList.count())]

            expr_sql = [self.exprList.item(i).text() for i in range(self.exprList.count())]

            select_items = (nonagg_sql + agg_sql + expr_sql) if (nonagg_sql or agg_sql or expr_sql) else ["*"]
            cols_sql = ", ".join(select_items)

            manual_where = self.edWhere.text().strip()
            sub_where = " AND ".join(self.subFilterStrings())
            if manual_where and sub_where:
                where_txt = f"({manual_where}) AND ({sub_where})"
            else:
                where_txt = manual_where or sub_where

            group_txt = self.edGroup.text().strip()
            having_txt = self.edHaving.text().strip()
            order_txt = self.edOrder.text().strip()

            parts = [f"SELECT {cols_sql} FROM {s}.{t}"]
            if where_txt:
                parts.append("WHERE " + where_txt)

            has_aggregates = len(agg_sql) > 0
            if self.cbAutoGroup.isChecked():
                need_group = has_aggregates or bool(having_txt)
                if need_group and not group_txt:
                    if nonagg_sql:
                        group_txt = ", ".join(nonagg_sql)
                    else:
                        group_txt = ""

            if group_txt:
                parts.append("GROUP BY " + group_txt)
            if having_txt:
                parts.append("HAVING " + having_txt)
            if order_txt:
                parts.append("ORDER BY " + order_txt)

            self.sqlView.setPlainText("\n".join(parts))
        except Exception as e:
            print("Ошибка в _gen_sql:", e)
            traceback.print_exc()

    def _run_sql(self):
        try:
            sql = self.sqlView.toPlainText().strip()
            if not sql.lower().startswith("select"):
                QMessageBox.warning(self, "SELECT", "Разрешён только SELECT")
                return
            try:
                cols, rows = db.preview(sql, limit=500)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка SELECT", f"Ошибка при выполнении запроса: {e}")
                return
            self.tbl.setColumnCount(len(cols));
            self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    self.tbl.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
        except Exception as e:
            print("Ошибка в _run_sql:", e)
            traceback.print_exc()

# --- Auto-GROUP BY patch appended ---

import re
import traceback

def __new_extract_columns_from_expr(self, exprs: list, available_cols: list) -> set:
    """
    Extract column names from SELECT expressions.
    - Finds quoted identifiers "name" and unquoted tokens matching available_cols (case-insensitive).
    Returns set of canonical column names (as found in available_cols).
    """
    cols = set()
    if not exprs:
        return cols

    # 1) quoted "name"
    for expr in exprs:
        if not expr:
            continue
        for m in re.finditer(r'"([^"]+)"', expr):
            name = m.group(1)
            cols.add(name)

    # 2) unquoted token matching available columns (case-insensitive)
    avail_lc = {c.lower(): c for c in available_cols}
    for expr in exprs:
        if not expr:
            continue
        for m in re.finditer(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', expr):
            token = m.group(1)
            if token.upper() in ("SELECT", "FROM", "AS", "CASE", "WHEN", "THEN", "ELSE",
                                 "END", "COALESCE", "NULLIF", "COUNT", "SUM", "AVG",
                                 "MIN", "MAX", "AND", "OR", "IN", "BETWEEN", "NOT", "EXISTS",
                                 "ANY", "ALL", "DISTINCT", "ON", "JOIN", "WHERE", "HAVING",
                                 "ORDER", "BY", "GROUP", "TRUE", "FALSE", "NULL"):
                continue
            if token.lower() in avail_lc:
                cols.add(avail_lc[token.lower()])
    return cols

def __new_gen_sql(self):
    try:
        s, t = self.cbTable.currentData() or (None, None)
        if s is None:
            QMessageBox.warning(self, "SELECT", "Выберите таблицу.")
            return

        # non-aggregated explicitly selected columns (from UI)
        nonagg_cols = [i.text() for i in self.colsList.selectedItems()]  # plain names
        nonagg_sql = [_id_quote(c) for c in nonagg_cols]

        # aggregate expressions (как строки), e.g. SUM("col") AS "alias"
        agg_sql = [self.selAggList.item(i).text() for i in range(self.selAggList.count())]

        # other expressions (CASE/COALESCE/NULLIF/... )
        expr_sql = [self.exprList.item(i).text() for i in range(self.exprList.count())]

        select_items = (nonagg_sql + agg_sql + expr_sql) if (nonagg_sql or agg_sql or expr_sql) else ["*"]
        cols_sql = ", ".join(select_items)

        manual_where = self.edWhere.text().strip()
        sub_where = " AND ".join(self.subFilterStrings())
        if manual_where and sub_where:
            where_txt = f"({manual_where}) AND ({sub_where})"
        else:
            where_txt = manual_where or sub_where

        group_txt = self.edGroup.text().strip()
        having_txt = self.edHaving.text().strip()
        order_txt = self.edOrder.text().strip()

        parts = [f"SELECT {cols_sql} FROM {s}.{t}"]
        if where_txt:
            parts.append("WHERE " + where_txt)

        has_aggregates = len(agg_sql) > 0
        if self.cbAutoGroup.isChecked():
            need_group = has_aggregates or bool(having_txt)
            if need_group and not group_txt:
                # Получим все доступные имена колонок таблицы (оригинальные имена)
                try:
                    available_cols = [c["column_name"] for c in db.list_columns(s, t)]
                except Exception:
                    # fallback: try attribute or empty
                    try:
                        available_cols = [c.name for c in db.list_columns(s, t)]
                    except Exception:
                        available_cols = []

                # 1) Извлечь колонки, используемые в выражениях SELECT (включая expr_sql и agg_sql)
                select_expr_strings = []
                select_expr_strings += nonagg_sql
                select_expr_strings += agg_sql
                select_expr_strings += expr_sql

                used_cols = __new_extract_columns_from_expr(self, select_expr_strings, available_cols)

                # 2) Выделим колонки, которые используются внутри агрегатов — их в GROUP BY не добавляем
                agg_cols = set()
                if agg_sql:
                    agg_cols = __new_extract_columns_from_expr(self, agg_sql, available_cols)

                # 3) Составим итоговый набор колонок для GROUP BY:
                final_cols = set(nonagg_cols) | (used_cols - agg_cols)

                final_cols = [c for c in final_cols if c]

                if final_cols:
                    group_txt = ", ".join([_id_quote(c) for c in final_cols])
                else:
                    group_txt = ""

        if group_txt:
            parts.append("GROUP BY " + group_txt)
        if having_txt:
            parts.append("HAVING " + having_txt)
        if order_txt:
            parts.append("ORDER BY " + order_txt)

        self.sqlView.setPlainText("\n".join(parts))
    except Exception as e:
        print("Ошибка в _gen_sql (patched):", e)
        traceback.print_exc()


# Bind patched functions into SelectBuilderDialog class if it exists
try:
    SelectBuilderDialog._extract_columns_from_expr = __new_extract_columns_from_expr
    SelectBuilderDialog._gen_sql = __new_gen_sql
except Exception:
    # If class is not defined at import-time, we'll attempt binding lazily when module is imported
    pass
