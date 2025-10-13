from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator

import db


FUNCS = {
    "UPPER(col)":      "UPPER({col})",
    "LOWER(col)":      "LOWER({col})",
    "SUBSTRING(col)":  "SUBSTRING({col} FROM %s FOR %s)",
    "TRIM(col)":       "TRIM({col})",
    "LPAD(col,n,ch)":  "LPAD({col}, %s, %s)",
    "RPAD(col,n,ch)":  "RPAD({col}, %s, %s)",
    "CONCAT(a,b)":     "CONCAT({col}, %s)",
    "col || suffix":   "({col} || %s)"
}

TEXTUAL_BASE_TYPES = {
    "text", "varchar", "character varying", "character", "char", "citext"
}


class StringFuncsDialog(QDialog):
    def __init__(self, parent=None, schema: str = "app", **kwargs):
        super().__init__(parent)
        self.setWindowTitle("Строковые функции")
        self.resize(900, 600)

        self._schema = schema
        self._int_validator = QIntValidator(0, 2147483647, self)
        self._col_types = {}

        root = QVBoxLayout(self)

        # Выбор таблицы и колонки
        trow = QHBoxLayout()
        trow.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        self.cbTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        trow.addWidget(self.cbTable, 1)

        trow.addWidget(QLabel("Колонка:"))
        self.cbColumn = QComboBox()
        self.cbColumn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        trow.addWidget(self.cbColumn, 1)

        root.addLayout(trow)

        # Выбор функции и параметры
        frow = QHBoxLayout()
        frow.addWidget(QLabel("Функция:"))
        self.cbFunc = QComboBox()
        self.cbFunc.addItems(list(FUNCS.keys()))
        self.cbFunc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frow.addWidget(self.cbFunc, 1)

        # Параметр 1
        self.lblP1 = QLabel("Параметр 1:")
        self.edP1 = QLineEdit()
        self.edP1.setClearButtonEnabled(True)
        self.edP1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frow.addWidget(self.lblP1)
        frow.addWidget(self.edP1, 1)

        # Параметр 2
        self.lblP2 = QLabel("Параметр 2:")
        self.edP2 = QLineEdit()
        self.edP2.setClearButtonEnabled(True)
        self.edP2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frow.addWidget(self.lblP2)
        frow.addWidget(self.edP2, 1)

        # Кнопки
        self.btnRun = QPushButton("Выполнить")
        self.btnClose = QPushButton("Закрыть")
        frow.addWidget(self.btnRun)
        frow.addWidget(self.btnClose)

        root.addLayout(frow)

        # Подсказка по типам
        self.lblHint = QLabel("")
        self.lblHint.setStyleSheet("color:#a33;")
        root.addWidget(self.lblHint)

        # Таблица результата
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(0)
        self.tbl.setRowCount(0)
        root.addWidget(self.tbl, 1)

        # Сигналы
        self.cbTable.currentIndexChanged.connect(self._onTableChanged)
        self.cbColumn.currentTextChanged.connect(self._updateRunState)
        self.cbFunc.currentTextChanged.connect(self._onFuncChanged)
        self.btnRun.clicked.connect(self._run)
        self.btnClose.clicked.connect(self.close)

        # Начальная загрузка
        self._loadTables()
        self._updateParamControls(self.cbFunc.currentText())
        self._updateRunState()

    # ------------------------- Загрузка данных справочников -------------------------

    def _loadTables(self):
        self.cbTable.clear()
        try:
            rows = db.list_tables(self._schema)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список таблиц: {e}")
            rows = []
        for schema, table in rows:
            self.cbTable.addItem(f"{schema}.{table}", (schema, table))

        if self.cbTable.count() > 0:
            self._onTableChanged(0)

    def _onTableChanged(self, idx: int):
        self.cbColumn.clear()
        self._col_types.clear()

        data = self.cbTable.currentData()
        if not data:
            return
        schema, table = data
        try:
            cols = db.list_columns(schema, table)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список колонок: {e}")
            return

        for c in cols:
            name = c.get("column_name")

            dtype = (
                c.get("data_type")
                or c.get("udt_name")
                or c.get("udt")
                or c.get("type")
                or ""
            )
            norm = str(dtype).lower().strip()
            self._col_types[name] = norm
            self.cbColumn.addItem(name)

        self._updateRunState()

    # ------------------------- Логика параметров (скрытие/валидация) -------------------------

    def _onFuncChanged(self, func: str):
        self._updateParamControls(func)
        self._updateRunState()

    def _updateParamControls(self, func: str):
        # Сброс
        self.edP1.setValidator(None)
        self.edP2.setValidator(None)
        self.edP1.clear()
        self.edP2.clear()
        self.edP1.setPlaceholderText("")
        self.edP2.setPlaceholderText("")

        # По умолчанию — скрыть оба
        def _set_p1_visible(flag: bool):
            self.lblP1.setVisible(flag)
            self.edP1.setVisible(flag)

        def _set_p2_visible(flag: bool):
            self.lblP2.setVisible(flag)
            self.edP2.setVisible(flag)

        _set_p1_visible(False)
        _set_p2_visible(False)

        if func.startswith("SUBSTRING"):
            # Нужны П1 (обязательный, целое) и П2 (опционально, целое)
            _set_p1_visible(True)
            _set_p2_visible(True)
            self.edP1.setPlaceholderText("Позиция начала (целое, обяз.)")
            self.edP2.setPlaceholderText("Длина (целое, опц.)")
            self.edP1.setValidator(self._int_validator)
            self.edP2.setValidator(self._int_validator)

        elif func.startswith("LPAD") or func.startswith("RPAD"):
            # Нужен П1 (обязательный, целое), П2 — опционально (строка)
            _set_p1_visible(True)
            _set_p2_visible(True)
            self.edP1.setPlaceholderText("Длина (целое, обяз.)")
            self.edP2.setPlaceholderText("Заполнитель (строка, опц.)")
            self.edP1.setValidator(self._int_validator)

        elif func.startswith("CONCAT") or func.startswith("col ||"):
            # Нужен только П1 (строка)
            _set_p1_visible(True)
            _set_p2_visible(False)
            self.edP1.setPlaceholderText("Суффикс/вторая часть (обяз.)")

        else:
            # UPPER/LOWER/TRIM — параметры не нужны (оба скрыты)
            _set_p1_visible(False)
            _set_p2_visible(False)

    # ------------------------- Ограничения по типам -------------------------

    def _function_requires_text(self, func: str) -> bool:
        return True

    def _column_is_textual(self, colname: str) -> bool:
        #Проверка, что столбец строковый
        dtype = (self._col_types.get(colname) or "").lower()
        if not dtype:
            return False
        if dtype.endswith("[]"):
            # массивы не поддерживаем
            return False
        base = dtype
        if "(" in base:
            base = base.split("(", 1)[0].strip()
        return base in TEXTUAL_BASE_TYPES

    def _updateRunState(self):
        func = self.cbFunc.currentText()
        col = self.cbColumn.currentText()
        need_text = self._function_requires_text(func)

        ok = True
        hint = ""
        if need_text:
            if not self._column_is_textual(col):
                ok = False
                hint = f"Функция «{func}» доступна только для строковых столбцов"

        self.btnRun.setEnabled(ok)
        self.lblHint.setText(hint)

    # ------------------------- Выполнение предпросмотра -------------------------

    def _run(self):
        #проверяем тип перед запуском
        func = self.cbFunc.currentText()
        colname = self.cbColumn.currentText()
        if self._function_requires_text(func) and not self._column_is_textual(colname):
            QMessageBox.warning(self, "Неверный тип столбца",
                                f"Нельзя применять «{func}» к нестроковому столбцу «{colname}».")
            return

        data = self.cbTable.currentData()
        if not data:
            QMessageBox.warning(self, "Внимание", "Выберите таблицу.")
            return
        schema, table = data
        if self.cbColumn.currentText().strip() == "":
            QMessageBox.warning(self, "Внимание", "Выберите колонку.")
            return

        col = f"\"{self.cbColumn.currentText()}\""
        p1_raw = self.edP1.text().strip()
        p2_raw = self.edP2.text().strip()

        # Утилита приведения типов
        def _to_int_or_error(raw: str, message: str) -> int:
            try:
                return int(raw)
            except ValueError:
                raise ValueError(message)

        # Базовый expr
        expr = FUNCS[func].format(col=col)
        params = []

        # Валидация и сбор параметров по функциям
        try:
            if func.startswith("SUBSTRING"):
                # П1 обязателен, целое; П2 — опционально, целое
                if not p1_raw:
                    raise ValueError("SUBSTRING: укажите начало (Параметр 1).")
                p1_int = _to_int_or_error(p1_raw, "SUBSTRING: «Параметр 1» должен быть целым числом.")
                if p2_raw:
                    p2_int = _to_int_or_error(p2_raw, "SUBSTRING: «Параметр 2» должен быть целым числом.")
                    expr = f"SUBSTRING({col} FROM %s FOR %s)"
                    params = [p1_int, p2_int]
                else:
                    expr = f"SUBSTRING({col} FROM %s)"
                    params = [p1_int]

            elif func.startswith("LPAD"):
                # П1 обязателен (целое), П2 опционален (строка)
                if not p1_raw:
                    raise ValueError("LPAD: укажите длину (Параметр 1).")
                p1_int = _to_int_or_error(p1_raw, "LPAD: «Параметр 1» должен быть целым числом.")
                if p2_raw:
                    expr = f"LPAD({col}, %s, %s)"
                    params = [p1_int, p2_raw]
                else:
                    expr = f"LPAD({col}, %s)"
                    params = [p1_int]

            elif func.startswith("RPAD"):
                # П1 обязателен (целое), П2 опционален (строка)
                if not p1_raw:
                    raise ValueError("RPAD: укажите длину (Параметр 1).")
                p1_int = _to_int_or_error(p1_raw, "RPAD: «Параметр 1» должен быть целым числом.")
                if p2_raw:
                    expr = f"RPAD({col}, %s, %s)"
                    params = [p1_int, p2_raw]
                else:
                    expr = f"RPAD({col}, %s)"
                    params = [p1_int]

            elif func.startswith("CONCAT") or func.startswith("col ||"):
                # Нужен один строковый параметр
                if not p1_raw:
                    raise ValueError("Для выбранной функции необходимо заполнить «Параметр 1».")
                params = [p1_raw]

            else:
                # UPPER/LOWER/TRIM — параметров нет
                params = []

        except ValueError as ve:
            QMessageBox.warning(self, "Неверный ввод", str(ve))
            return

        sql = f"SELECT {col} AS original, {expr} AS transformed FROM {schema}.{table}"
        try:
            cols, rows = db.preview(sql, limit=300, params=tuple(params))
            self.tbl.setColumnCount(len(cols))
            self.tbl.setHorizontalHeaderLabels(cols)
            self.tbl.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, v in enumerate(row):
                    self.tbl.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка функции", str(e))
