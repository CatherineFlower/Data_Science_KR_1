import traceback
from functools import partial  # Добавлен импорт для надежного подключения кнопок
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QCheckBox, QTabWidget, QWidget, QInputDialog, QGroupBox)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
import re
import db

_AGG_FUNCS = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
_CMP_OPS_WITH_VALUE = [">=", ">", "=", "<=", "<", "<>", "BETWEEN", "NOT BETWEEN", "IN", "NOT IN"]
_CMP_OPS_NO_VALUE = ["IS NULL", "IS NOT NULL"]
_SUBQUERY_CMP_OPS = [">=", ">", "=", "<=", "<", "<>"]
_QTY = ["ANY", "ALL"]


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
        self.setWindowTitle("Конструктор запросов (CTE, Views, Grouping)")
        self.setMinimumSize(1600, 1000)

        # --- Валидаторы ---
        self._alias_validator = QRegExpValidator(QRegExp(r'^[a-zA-Z_][a-zA-Z0-9_]*$'))
        self._sql_fragment_validator = QRegExpValidator(QRegExp(r'^[^"\'/\\|`=?!~+<>:;-]*$'))
        self._sql_where_validator = QRegExpValidator(QRegExp(r'^[^"\'/\\|`?!~+:;-]*$'))

        # Хранилище CTE: список кортежей (name, sql_body)
        self.cte_list_data = []

        self._set_default_styles()

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # -----------------------------------------------------------
        # ТАБ 0: CTE (Common Table Expressions)
        # -----------------------------------------------------------
        self.tab_cte = QWidget()
        self._init_cte_tab()
        self.tabs.addTab(self.tab_cte, "CTE (WITH)")

        # -----------------------------------------------------------
        # ТАБ 1: Основное (SELECT)
        # -----------------------------------------------------------
        self.tab_main = QWidget()
        self._init_main_tab()
        self.tabs.addTab(self.tab_main, "SELECT")

        # -----------------------------------------------------------
        # ТАБ 2: Фильтры и Группировка
        # -----------------------------------------------------------
        self.tab_filters = QWidget()
        self._init_filters_tab()
        self.tabs.addTab(self.tab_filters, "WHERE / GROUP BY")

        # -----------------------------------------------------------
        # ТАБ 3: Подзапросы
        # -----------------------------------------------------------
        self.tab_subq = QWidget()
        self._init_subq_tab()
        self.tabs.addTab(self.tab_subq, "Подзапросы")

        # -----------------------------------------------------------
        # ТАБ 4: Выражения
        # -----------------------------------------------------------
        self.tab_expr = QWidget()
        self._init_expr_tab()
        self.tabs.addTab(self.tab_expr, "Выражения (Case/Coalesce)")

        # -----------------------------------------------------------
        # ТАБ 5: Результат и Создание View
        # -----------------------------------------------------------
        self.tab_result = QWidget()
        self._init_result_tab()
        self.tabs.addTab(self.tab_result, "Результат / VIEW")

        # Инициализация данных
        self._load_tables()
        self._load_columns()
        self._load_inner_columns()
        self._toggle_sub_ui()

    def _set_default_styles(self):
        # Оставляем ваши стили без изменений для краткости
        self.setStyleSheet("""
            QDialog { background-color: rgba(16, 30, 41, 240); color: white; }
            QLabel { color: white; font-size: 13px; padding: 8px; font-weight: bold; }
            QComboBox { background-color: rgba(25, 45, 60, 200); color: white; border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; padding: 12px; min-height: 40px; font-size: 24px; }
            QComboBox:hover { border: 1px solid rgba(66, 122, 160, 255); }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid white; margin-right: 10px; }
            QComboBox QAbstractItemView { background-color: rgba(25, 45, 60, 255); color: white; border: 1px solid rgba(46, 82, 110, 255); selection-background-color: rgba(2, 65, 118, 255); font-size: 14px; padding: 12px; outline: none; }
            QComboBox QAbstractItemView::item { min-height: 30px; padding: 8px; }
            QLineEdit { background-color: rgba(25, 45, 60, 200); color: white; border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; padding: 10px; font-size: 13px; min-height: 20px; font-weight: bold; }
            QLineEdit:focus { border: 1px solid rgba(66, 122, 160, 255); }
            QLineEdit:invalid { border: 2px solid rgba(200, 80, 80, 255); }
            QLineEdit::placeholder { color: rgba(200, 200, 200, 150); font-size: 12px; font-weight: bold; }
            QTextEdit { background-color: rgba(25, 45, 60, 200); color: white; border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; padding: 10px; font-size: 13px; font-family: 'Courier New', monospace; font-weight: bold; }
            QTextEdit:focus { border: 1px solid rgba(66, 122, 160, 255); }
            QTableWidget { background-color: rgba(25, 45, 60, 200); color: white; border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; gridline-color: rgba(46, 82, 110, 150); font-size: 22px; font-weight: bold; outline: none; }
            QTableWidget::item { background-color: transparent; color: white; border-bottom: 1px solid rgba(46, 82, 110, 100); padding: 8px; font-weight: bold; }
            QTableWidget::item:selected { background-color: rgba(2, 65, 118, 200); color: white; }
            QTableWidget::item:hover { background-color: rgba(45, 65, 85, 200); }
            QHeaderView::section { background-color: rgba(2, 65, 118, 255); color: white; border: none; padding: 8px; font-weight: bold; font-size: 13px; border-right: 1px solid rgba(46, 82, 110, 255); border-bottom: 1px solid rgba(46, 82, 110, 255); }
            QHeaderView::section:last { border-right: none; }
            QHeaderView::section:hover { background-color: rgba(2, 65, 118, 200); }
            QHeaderView::section:pressed { background-color: rgba(2, 65, 118, 100); }
            QListWidget { background-color: rgba(25, 45, 60, 200); color: white; border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; font-size: 20px; font-weight: bold; outline: none; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid rgba(46, 82, 110, 100); }
            QListWidget::item:selected { background-color: rgba(2, 65, 118, 255); color: white; }
            QListWidget::item:hover { background-color: rgba(35, 55, 75, 200); }
            QPushButton { background-color: rgba(2, 65, 118, 255); color: rgba(255, 255, 255, 200); border-radius: 5px; padding: 12px; min-height: 40px; min-width: 120px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(2, 65, 118, 200); }
            QPushButton:pressed { background-color: rgba(2, 65, 118, 100); }
            QScrollBar:vertical { border: none; background-color: rgba(25, 45, 60, 200); width: 12px; margin: 0px; }
            QScrollBar:handle:vertical { background-color: rgba(46, 82, 110, 150); border-radius: 6px; min-height: 20px; }
            QScrollBar:handle:vertical:hover { background-color: rgba(46, 82, 110, 200); }
            QScrollBar:horizontal { border: none; background-color: rgba(25, 45, 60, 200); height: 12px; margin: 0px; }
            QScrollBar:handle:horizontal { background-color: rgba(46, 82, 110, 150); border-radius: 6px; min-width: 20px; }
            QScrollBar:handle:horizontal:hover { background-color: rgba(46, 82, 110, 200); }
            QTableView { background-color: rgba(25, 45, 60, 200); color: white; gridline-color: rgba(46, 82, 110, 150); selection-background-color: rgba(2, 65, 118, 200); selection-color: white; outline: none; }
            QTableView::item { background-color: transparent; color: white; border-bottom: 1px solid rgba(46, 82, 110, 100); padding: 8px; }
            QTableCornerButton::section { background-color: rgba(2, 65, 110, 255); border: none; }
            QAbstractScrollArea { background-color: rgba(25, 45, 60, 200); }
            QTabWidget::pane { border: 1px solid rgba(46, 82, 110, 255); background-color: rgba(16, 30, 41, 240); }
            QTabBar::tab { background-color: rgba(25, 45, 60, 200); color: white; padding: 16px 24px; margin-right: 2px; font-size: 13px; font-weight: bold; border: 1px solid rgba(46, 82, 110, 255); border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: rgba(2, 65, 118, 255); border-color: rgba(66, 122, 160, 255); }
            QTabBar::tab:hover:!selected { background-color: rgba(2, 65, 118, 150); }
            QCheckBox { color: white; font-size: 13px; spacing: 10px; font-weight: bold; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid rgba(46, 82, 110, 255); border-radius: 3px; background-color: rgba(25, 45, 60, 200); }
            QCheckBox::indicator:checked { background-color: rgba(2, 65, 118, 255); }
            QCheckBox::indicator:hover { border: 1px solid rgba(66, 122, 160, 255); }
            QGroupBox { border: 1px solid rgba(46, 82, 110, 255); border-radius: 4px; margin-top: 20px; font-weight: bold; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; color: white; }
        """)

    # ----------------------------------------------------------------------
    # UI INITIALIZATION METHODS
    # ----------------------------------------------------------------------

    def _init_cte_tab(self):
        layout = QVBoxLayout(self.tab_cte)
        layout.addWidget(QLabel("Управление Common Table Expressions (WITH)"))
        
        info = QLabel("Вы можете создать CTE вручную или собрать запрос во вкладках 'SELECT/WHERE' и нажать 'Сохранить текущий запрос как CTE'.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Список CTE
        self.listCTE = QListWidget()
        layout.addWidget(self.listCTE, 1)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btnCteFromCurrent = QPushButton("Сохранить ТЕКУЩУЮ конфигурацию как CTE")
        self.btnCteDelete = QPushButton("Удалить выбранный CTE")
        self.btnCteClear = QPushButton("Очистить все CTE")
        
        btn_layout.addWidget(self.btnCteFromCurrent)
        btn_layout.addWidget(self.btnCteDelete)
        btn_layout.addWidget(self.btnCteClear)
        layout.addLayout(btn_layout)

        self.btnCteFromCurrent.clicked.connect(self._add_cte_from_current)
        self.btnCteDelete.clicked.connect(self._delete_cte)
        self.btnCteClear.clicked.connect(self._clear_ctes)

    def _init_main_tab(self):
        layout = QVBoxLayout(self.tab_main)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        self.cbTable.currentIndexChanged.connect(self._load_columns)
        hl.addWidget(self.cbTable, 1)
        layout.addLayout(hl)

        layout.addWidget(QLabel("Столбцы (SELECT — неагрегированные):"))
        self.colsList = QListWidget()
        self.colsList.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.colsList, 2)

        layout.addWidget(QLabel("Агрегаты (SELECT — добавляются отдельными выражениями):"))
        aggRow = QHBoxLayout()
        self.cbSelAggFunc = QComboBox()
        self.cbSelAggFunc.addItems(_AGG_FUNCS)
        self.cbSelAggCol = QComboBox()
        self.cbSelAggDistinct = QCheckBox("DISTINCT")
        self.edSelAggAlias = QLineEdit()
        self.edSelAggAlias.setPlaceholderText("Псевдоним (alias), опционально")
        self.edSelAggAlias.setValidator(self._alias_validator)
        
        self.btnSelAggAdd = QPushButton("Добавить в SELECT")
        self.btnSelAggDel = QPushButton("Удалить выбранные")

        aggRow.addWidget(QLabel("Функция"))
        aggRow.addWidget(self.cbSelAggFunc)
        aggRow.addWidget(QLabel("Столбец"))
        aggRow.addWidget(self.cbSelAggCol)
        aggRow.addWidget(self.cbSelAggDistinct)
        aggRow.addWidget(QLabel("Алиас"))
        aggRow.addWidget(self.edSelAggAlias)
        aggRow.addWidget(self.btnSelAggAdd)
        aggRow.addWidget(self.btnSelAggDel)
        layout.addLayout(aggRow)

        self.selAggList = QListWidget()
        layout.addWidget(self.selAggList, 1)

        self.btnSelAggAdd.clicked.connect(self._add_select_agg)
        self.btnSelAggDel.clicked.connect(self._del_select_agg)

    def _init_filters_tab(self):
        layout = QVBoxLayout(self.tab_filters)

        # WHERE
        layout.addWidget(QLabel("WHERE (без слова WHERE)"))
        self.edWhere = QLineEdit()
        self.edWhere.setPlaceholderText("Например: status = 'active' AND price > 100")
        self.edWhere.setValidator(self._sql_where_validator)
        layout.addWidget(self.edWhere)

        # GROUP BY SECTION
        grp_box = QGroupBox("Настройка Группировки (GROUP BY)")
        grp_layout = QVBoxLayout(grp_box)
        
        # Тип группировки
        row_gtype = QHBoxLayout()
        row_gtype.addWidget(QLabel("Тип:"))
        self.cbGroupType = QComboBox()
        self.cbGroupType.addItems(["Автоматически (Simple)", "SIMPLE (Явно)", "ROLLUP", "CUBE", "GROUPING SETS"])
        row_gtype.addWidget(self.cbGroupType)
        grp_layout.addLayout(row_gtype)

        grp_layout.addWidget(QLabel("Выберите столбцы для группировки:"))
        self.listGroupCols = QListWidget()
        self.listGroupCols.setSelectionMode(QListWidget.MultiSelection)
        grp_layout.addWidget(self.listGroupCols)

        layout.addWidget(grp_box)

        # HAVING
        layout.addWidget(QLabel("HAVING — конструктор"))
        row_hav = QHBoxLayout()
        self.cbHavingFunc = QComboBox()
        self.cbHavingFunc.addItems(_AGG_FUNCS)
        self.cbHavingColumn = QComboBox()
        self.cbHavingOp = QComboBox()
        self.cbHavingOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
        self.edHavingValue = QLineEdit()
        self.edHavingValue.setPlaceholderText("значение")
        self.btnHavingAdd = QPushButton("Добавить")
        self.btnHavingDel = QPushButton("Удалить выбранные")

        row_hav.addWidget(QLabel("Функция"))
        row_hav.addWidget(self.cbHavingFunc)
        row_hav.addWidget(QLabel("Столбец"))
        row_hav.addWidget(self.cbHavingColumn)
        row_hav.addWidget(QLabel("Оператор"))
        row_hav.addWidget(self.cbHavingOp)
        row_hav.addWidget(QLabel("Значение"))
        row_hav.addWidget(self.edHavingValue)
        row_hav.addWidget(self.btnHavingAdd)
        row_hav.addWidget(self.btnHavingDel)
        layout.addLayout(row_hav)

        self.havingList = QListWidget()
        layout.addWidget(self.havingList)

        # ORDER BY
        layout.addWidget(QLabel("ORDER BY"))
        self.edOrder = QLineEdit()
        self.edOrder.setPlaceholderText("column1 DESC, column2 ASC")
        layout.addWidget(self.edOrder)

        self.btnHavingAdd.clicked.connect(self._add_having)
        self.btnHavingDel.clicked.connect(self._del_having)
        self.cbHavingOp.currentIndexChanged.connect(lambda: self.edHavingValue.setEnabled(self.cbHavingOp.currentText() in _CMP_OPS_WITH_VALUE))

    def _init_subq_tab(self):
        layout = QVBoxLayout(self.tab_subq)
        layout.addWidget(QLabel("WHERE — подзапросы (ANY/ALL/EXISTS)"))
        
        row_top = QHBoxLayout()
        self.cbSubKind = QComboBox()
        self.cbSubKind.addItems(["EXISTS", "NOT EXISTS", "Сравнение с ANY/ALL"])
        self.cbSubKind.currentIndexChanged.connect(self._toggle_sub_ui)
        self.cbLeftCol = QComboBox()
        self.cbCmpOp = QComboBox()
        self.cbCmpOp.addItems(_SUBQUERY_CMP_OPS)
        self.cbQuantifier = QComboBox()
        self.cbQuantifier.addItems(_QTY)
        
        row_top.addWidget(QLabel("Тип"))
        row_top.addWidget(self.cbSubKind)
        row_top.addWidget(QLabel("Внешний столбец"))
        row_top.addWidget(self.cbLeftCol)
        row_top.addWidget(QLabel("Оператор"))
        row_top.addWidget(self.cbCmpOp)
        row_top.addWidget(QLabel("Квантор"))
        row_top.addWidget(self.cbQuantifier)
        layout.addLayout(row_top)

        row_tbl = QHBoxLayout()
        self.cbInnerTable = QComboBox()
        self.cbInnerTable.currentIndexChanged.connect(self._load_inner_columns)
        self.cbInnerCol = QComboBox()
        row_tbl.addWidget(QLabel("Подзапрос: таблица"))
        row_tbl.addWidget(self.cbInnerTable)
        row_tbl.addWidget(QLabel("Столбец в подзапросе"))
        row_tbl.addWidget(self.cbInnerCol)
        layout.addLayout(row_tbl)

        row_corr = QHBoxLayout()
        self.cbCorrOuter = QComboBox()
        self.cbCorrInner = QComboBox()
        self.btnCorrAdd = QPushButton("Добавить связь")
        self.btnCorrDel = QPushButton("Удалить связь")
        row_corr.addWidget(QLabel("Связь: внешний"))
        row_corr.addWidget(self.cbCorrOuter)
        row_corr.addWidget(QLabel("="))
        row_corr.addWidget(self.cbCorrInner)
        row_corr.addWidget(self.btnCorrAdd)
        row_corr.addWidget(self.btnCorrDel)
        layout.addLayout(row_corr)
        self.corrList = QListWidget()
        layout.addWidget(self.corrList)

        row_btn = QHBoxLayout()
        self.btnSubAdd = QPushButton("Добавить фильтр в WHERE")
        self.btnSubDel = QPushButton("Удалить выбранные")
        row_btn.addWidget(self.btnSubAdd)
        row_btn.addWidget(self.btnSubDel)
        layout.addLayout(row_btn)
        
        self.subFilterList = QListWidget()
        layout.addWidget(self.subFilterList)

        self.btnCorrAdd.clicked.connect(self._add_corr)
        self.btnCorrDel.clicked.connect(self._del_corr)
        self.btnSubAdd.clicked.connect(self._add_subfilter)
        self.btnSubDel.clicked.connect(self._del_subfilter)

    def _init_expr_tab(self):
        layout = QVBoxLayout(self.tab_expr)
        
        gb_case = QGroupBox("CASE Builder")
        l_case = QVBoxLayout(gb_case)
        
        r1 = QHBoxLayout()
        self.edCaseAlias = QLineEdit()
        self.edCaseAlias.setPlaceholderText("Алиас результирующего столбца")
        r1.addWidget(QLabel("Алиас"))
        r1.addWidget(self.edCaseAlias)
        l_case.addLayout(r1)

        r2 = QHBoxLayout()
        self.cbWhenCol = QComboBox()
        self.cbWhenOp = QComboBox()
        self.cbWhenOp.addItems(_CMP_OPS_WITH_VALUE + _CMP_OPS_NO_VALUE)
        self.edWhenVal = QLineEdit()
        self.edWhenVal.setPlaceholderText("значение")
        self.edThenVal = QLineEdit()
        self.edThenVal.setPlaceholderText("THEN значение")
        self.btnWhenAdd = QPushButton("Добавить WHEN-THEN")
        r2.addWidget(QLabel("WHEN"))
        r2.addWidget(self.cbWhenCol)
        r2.addWidget(self.cbWhenOp)
        r2.addWidget(self.edWhenVal)
        r2.addWidget(QLabel("THEN"))
        r2.addWidget(self.edThenVal)
        r2.addWidget(self.btnWhenAdd)
        l_case.addLayout(r2)
        
        self.caseWhenList = QListWidget()
        l_case.addWidget(self.caseWhenList)

        r3 = QHBoxLayout()
        self.edElseVal = QLineEdit()
        self.edElseVal.setPlaceholderText("ELSE значение (опционально)")
        self.btnCaseAddExpr = QPushButton("Добавить CASE в SELECT")
        r3.addWidget(QLabel("ELSE"))
        r3.addWidget(self.edElseVal)
        r3.addWidget(self.btnCaseAddExpr)
        l_case.addLayout(r3)
        
        layout.addWidget(gb_case)

        layout.addWidget(QLabel("Выражения для SELECT"))
        self.exprList = QListWidget()
        layout.addWidget(self.exprList)
        self.btnExprDel = QPushButton("Удалить выбранные выражения")
        self.btnExprDel.clicked.connect(self._del_expr)
        layout.addWidget(self.btnExprDel)

        self.btnWhenAdd.clicked.connect(self._add_case_when)
        self.btnCaseAddExpr.clicked.connect(self._add_case_expr)

    def _init_result_tab(self):
        layout = QVBoxLayout(self.tab_result)

        h_gen = QHBoxLayout()
        self.btnGenerate = QPushButton("Сгенерировать SQL")
        self.btnGenerate.setStyleSheet("background-color: #2E7D32;")
        h_gen.addWidget(self.btnGenerate)
        layout.addLayout(h_gen)

        self.sqlView = QTextEdit()
        layout.addWidget(self.sqlView, 1)

        h_acts = QHBoxLayout()
        self.btnRun = QPushButton("Выполнить и показать")
        self.btnCreateView = QPushButton("Создать VIEW")
        self.btnCreateMatView = QPushButton("Создать MAT VIEW")
        
        h_acts.addWidget(self.btnRun)
        h_acts.addWidget(self.btnCreateView)
        h_acts.addWidget(self.btnCreateMatView)
        layout.addLayout(h_acts)

        self.tbl = QTableWidget()
        layout.addWidget(self.tbl, 3)

        self.btnGenerate.clicked.connect(self._gen_sql_ui)
        self.btnRun.clicked.connect(self._run_sql)
        
        # --- FIX: Использование partial для безопасной передачи флага is_mat ---
        self.btnCreateView.clicked.connect(partial(self._create_view_handler, is_mat=False))
        self.btnCreateMatView.clicked.connect(partial(self._create_view_handler, is_mat=True))

    # ----------------------------------------------------------------------
    # LOAD DATA
    # ----------------------------------------------------------------------

    def _load_tables(self):
        try:
            self.cbTable.clear()
            self.cbInnerTable.clear()
            tables = list(db.list_tables(self.schema))
            for s, t in tables:
                text = f"{s}.{t}"
                self.cbTable.addItem(text, (s, t))
                self.cbInnerTable.addItem(text, (s, t))
        except Exception:
            pass

    def _load_columns(self):
        self.colsList.clear()
        self.listGroupCols.clear()
        self.cbSelAggCol.clear()
        self.cbSelAggCol.addItem("*")
        self.cbHavingColumn.clear()
        self.cbHavingColumn.addItem("*")
        self.cbLeftCol.clear()
        self.cbCorrOuter.clear()
        self.cbWhenCol.clear()

        s, t = self.cbTable.currentData() or (None, None)
        if not s: return

        try:
            cols = db.list_columns(s, t)
            for c in cols:
                name = c["column_name"]
                
                item = QListWidgetItem(name)
                item.setSelected(True)
                self.colsList.addItem(item)
                
                g_item = QListWidgetItem(name)
                self.listGroupCols.addItem(g_item)

                self.cbSelAggCol.addItem(name)
                self.cbHavingColumn.addItem(name)
                self.cbLeftCol.addItem(name)
                self.cbCorrOuter.addItem(name)
                self.cbWhenCol.addItem(name)
                
        except Exception as e:
            print(e)

    def _load_inner_columns(self):
        self.cbInnerCol.clear()
        self.cbCorrInner.clear()
        s, t = self.cbInnerTable.currentData() or (None, None)
        if not s: return
        try:
            for c in db.list_columns(s, t):
                name = c["column_name"]
                self.cbInnerCol.addItem(name)
                self.cbCorrInner.addItem(name)
        except: pass

    # ----------------------------------------------------------------------
    # CTE LOGIC
    # ----------------------------------------------------------------------
    def _add_cte_from_current(self):
        sql = self._generate_select_sql_string()
        if not sql: return

        name, ok = QInputDialog.getText(self, "Новый CTE", "Введите имя для CTE (alias):")
        if ok and name:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                QMessageBox.warning(self, "Ошибка", "Некорректное имя CTE.")
                return
            
            self.cte_list_data.append((name, sql))
            self.listCTE.addItem(f"{name} AS (...)")
            QMessageBox.information(self, "CTE", f"CTE '{name}' добавлен. Теперь вы можете очистить форму и использовать его.")
            self.cbTable.addItem(f"CTE: {name}", ("CTE", name))

    def _delete_cte(self):
        row = self.listCTE.currentRow()
        if row >= 0:
            self.cte_list_data.pop(row)
            self.listCTE.takeItem(row)

    def _clear_ctes(self):
        self.cte_list_data = []
        self.listCTE.clear()

    # ----------------------------------------------------------------------
    # LOGIC HELPERS
    # ----------------------------------------------------------------------

    def _add_select_agg(self):
        func = self.cbSelAggFunc.currentText().strip()
        col = self.cbSelAggCol.currentText().strip()
        is_dist = self.cbSelAggDistinct.isChecked()
        alias = self.edSelAggAlias.text().strip()
        
        inner = f"DISTINCT {_id_quote(col)}" if is_dist else (f"{_id_quote(col)}" if col != "*" else "*")
        expr = f"{func}({inner})"
        if alias: expr += f" AS {_id_quote(alias)}"
        self.selAggList.addItem(expr)

    def _del_select_agg(self):
        for i in self.selAggList.selectedItems():
            self.selAggList.takeItem(self.selAggList.row(i))

    def _add_having(self):
        func = self.cbHavingFunc.currentText().strip()
        col = self.cbHavingColumn.currentText().strip()
        op = self.cbHavingOp.currentText().strip()
        val = self.edHavingValue.text().strip()
        
        col_expr = "*" if col == "*" else _id_quote(col)
        expr = f"{func}({col_expr}) {op} {val}"
        self.havingList.addItem(expr)

    def _del_having(self):
        for i in self.havingList.selectedItems():
            self.havingList.takeItem(self.havingList.row(i))

    def _toggle_sub_ui(self):
        kind = self.cbSubKind.currentText()
        is_any_all = "ANY/ALL" in kind
        self.cbLeftCol.setEnabled(is_any_all)
        self.cbCmpOp.setEnabled(is_any_all)
        self.cbQuantifier.setEnabled(is_any_all)

    def _add_corr(self):
        o = self.cbCorrOuter.currentText()
        i = self.cbCorrInner.currentText()
        if o and i: self.corrList.addItem(f"{_id_quote(o)} = sq.{_id_quote(i)}")

    def _del_corr(self):
        for i in self.corrList.selectedItems(): self.corrList.takeItem(self.corrList.row(i))

    def _add_subfilter(self):
        kind = self.cbSubKind.currentText()
        s, t = self.cbInnerTable.currentData()
        inner_from = f"{s}.{t}"
        corrs = [self.corrList.item(k).text() for k in range(self.corrList.count())]
        where_clause = ("WHERE " + " AND ".join(corrs)) if corrs else ""
        
        sub_sql = ""
        if "EXISTS" in kind:
            sub_sql = f"{kind} (SELECT 1 FROM {inner_from} AS sq {where_clause})"
        else:
            left = self.cbLeftCol.currentText()
            op = self.cbCmpOp.currentText()
            q = self.cbQuantifier.currentText()
            inner_col = self.cbInnerCol.currentText()
            sub_sql = f"{_id_quote(left)} {op} {q} (SELECT {_id_quote(inner_col)} FROM {inner_from} AS sq {where_clause})"
        
        self.subFilterList.addItem(sub_sql)

    def _del_subfilter(self):
        for i in self.subFilterList.selectedItems(): self.subFilterList.takeItem(self.subFilterList.row(i))

    def _add_case_when(self):
        c = self.cbWhenCol.currentText()
        op = self.cbWhenOp.currentText()
        v = self.edWhenVal.text()
        t = self.edThenVal.text()
        if t:
            self.caseWhenList.addItem(f"WHEN {_id_quote(c)} {op} {v} THEN {t}")

    def _add_case_expr(self):
        if self.caseWhenList.count() == 0: return
        parts = ["CASE"]
        for i in range(self.caseWhenList.count()):
            parts.append(self.caseWhenList.item(i).text())
        else_val = self.edElseVal.text()
        if else_val: parts.append(f"ELSE {else_val}")
        parts.append("END")
        
        full = " ".join(parts)
        alias = self.edCaseAlias.text()
        if alias: full += f" AS {_id_quote(alias)}"
        self.exprList.addItem(full)
        self.caseWhenList.clear()

    def _del_expr(self):
        for i in self.exprList.selectedItems(): self.exprList.takeItem(self.exprList.row(i))

    # ----------------------------------------------------------------------
    # SQL GENERATION
    # ----------------------------------------------------------------------

    def _generate_select_sql_string(self):
        s, t = self.cbTable.currentData() or (None, None)
        if not s and not t:
            txt = self.cbTable.currentText()
            if txt.startswith("CTE: "):
                s, t = "CTE", txt.replace("CTE: ", "")
            else:
                return None

        sel_cols = [item.text() for item in self.colsList.selectedItems()]
        sel_cols_quoted = [_id_quote(c) for c in sel_cols]
        
        aggs = [self.selAggList.item(i).text() for i in range(self.selAggList.count())]
        exprs = [self.exprList.item(i).text() for i in range(self.exprList.count())]
        
        all_cols = sel_cols_quoted + aggs + exprs
        if not all_cols: all_cols = ["*"]
        
        select_clause = f"SELECT {', '.join(all_cols)}"
        
        from_clause = f"FROM {t}" if s == "CTE" else f"FROM {s}.{t}"
        
        wheres = []
        w_man = self.edWhere.text().strip()
        if w_man: wheres.append(f"({w_man})")
        for i in range(self.subFilterList.count()):
            wheres.append(f"({self.subFilterList.item(i).text()})")
            
        where_clause = ("WHERE " + " AND ".join(wheres)) if wheres else ""

        group_clause = ""
        g_type = self.cbGroupType.currentText()
        
        g_cols = [item.text() for item in self.listGroupCols.selectedItems()]
        g_cols_quoted = [_id_quote(c) for c in g_cols]

        if "Simple" in g_type:
            if not g_cols and "Авто" in g_type and aggs:
                g_cols_quoted = sel_cols_quoted
            
            if g_cols_quoted:
                group_clause = "GROUP BY " + ", ".join(g_cols_quoted)

        elif g_type in ["ROLLUP", "CUBE"]:
            if g_cols_quoted:
                group_clause = f"GROUP BY {g_type} (" + ", ".join(g_cols_quoted) + ")"
        
        elif g_type == "GROUPING SETS":
            if g_cols_quoted:
                sets = [f"({c})" for c in g_cols_quoted]
                sets.append("()")
                group_clause = f"GROUP BY GROUPING SETS ({', '.join(sets)})"

        havs = [self.havingList.item(i).text() for i in range(self.havingList.count())]
        having_clause = ("HAVING " + " AND ".join(havs)) if havs else ""

        ord_txt = self.edOrder.text().strip()
        order_clause = f"ORDER BY {ord_txt}" if ord_txt else ""

        parts = [select_clause, from_clause, where_clause, group_clause, having_clause, order_clause]
        return "\n".join([p for p in parts if p])

    def _gen_sql_ui(self):
        main_sql = self._generate_select_sql_string()
        if not main_sql:
            QMessageBox.warning(self, "Ошибка", "Не выбрана таблица или столбцы")
            return

        final_sql = ""
        if self.cte_list_data:
            cte_parts = []
            for name, body in self.cte_list_data:
                cte_parts.append(f"{name} AS (\n{body}\n)")
            final_sql += "WITH " + ",\n".join(cte_parts) + "\n"
        
        final_sql += main_sql
        self.sqlView.setPlainText(final_sql)

    def _run_sql(self):
        sql = self.sqlView.toPlainText()
        if not sql: return
        try:
            cols, rows = db.preview(sql)
            self.tbl.setColumnCount(len(cols))
            self.tbl.setRowCount(len(rows))
            self.tbl.setHorizontalHeaderLabels(cols)
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.tbl.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка SQL", str(e))

    def _create_view_handler(self, is_mat=False):
        """
        Обработчик создания VIEW / MATERIALIZED VIEW
        """
        sql = self.sqlView.toPlainText()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте SQL.")
            return

        type_str = "MATERIALIZED VIEW" if is_mat else "VIEW"
        name, ok = QInputDialog.getText(self, f"Создание {type_str}", "Введите имя представления:")
        
        if ok and name:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                QMessageBox.warning(self, "Ошибка", "Некорректное имя.")
                return
            
            try:
                # ВАЖНО: Мы принудительно передаем is_mat, чтобы избежать путаницы
                db.create_view_from_select(self.schema, name, sql, is_mat)
                QMessageBox.information(self, "Успех", f"{type_str} '{name}' успешно создано.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось создать представление:\n{e}")