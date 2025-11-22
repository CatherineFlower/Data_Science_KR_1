from __future__ import annotations

from typing import List, Tuple

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator  # <-- Добавлено
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import db

_SQL_LIST_TYPES = """
                  SELECT t.oid,
                         n.nspname AS schema,
       t.typname AS name,
       t.typtype AS kind,    -- 'e' enum, 'c' composite, 'd' domain, 'r' range, etc
       CASE t.typtype
         WHEN 'e' THEN 'ENUM'
         WHEN 'c' THEN 'COMPOSITE'
         WHEN 'd' THEN 'DOMAIN'
         WHEN 'r' THEN 'RANGE'
         ELSE t.typtype::text
                  END \
                  AS kind_readable
FROM pg_type t
JOIN pg_namespace n ON n.oid = t.typnamespace
LEFT JOIN pg_class cl ON cl.oid = t.typrelid
WHERE n.nspname = \
                  %s
                  AND \
                  t \
                  . \
                  typtype \
                  IN \
                  ( \
                  'e', \
                  'c' \
                  )
                  AND \
                  t \
                  . \
                  typisdefined
                  AND \
                  ( \
                  t \
                  . \
                  typtype \
                  <> \
                  'c' \
                  OR \
                  cl \
                  . \
                  relkind \
                  = \
                  'c' \
                  )
                  ORDER \
                  BY \
                  kind_readable, \
                  name \
                  """

_SQL_ENUM_LABELS = """
                   SELECT enumlabel
                   FROM pg_enum e
                   WHERE e.enumtypid = %s
                   ORDER BY e.enumsortorder \
                   """

_SQL_COMPOSITE_ATTRS = """
                       SELECT a.attname                            AS name,
                              format_type(a.atttypid, a.atttypmod) AS type,
                              a.attnum                             AS pos
                       FROM pg_attribute a
                                JOIN pg_type t ON t.typrelid = a.attrelid
                       WHERE t.oid = %s
                         AND a.attnum > 0 \
                         AND NOT a.attisdropped
                       ORDER BY a.attnum \
                       """


def list_user_defined_types(schema: str) -> list[dict]:
    cols, rows = db.run_select(_SQL_LIST_TYPES, (schema,))
    return [dict(zip(cols, r)) for r in rows]


def list_enum_labels(type_oid: int) -> List[str]:
    return [r[0] for r in db.run_select(_SQL_ENUM_LABELS, (type_oid,))[1]]


def list_composite_attrs(type_oid: int) -> List[Tuple[str, str, int]]:
    return [(r[0], r[1], r[2]) for r in db.run_select(_SQL_COMPOSITE_ATTRS, (type_oid,))[1]]


# --- Dialog ---

class UserTypesDialog(QDialog):
    """GUI-менеджер пользовательских типов (ENUM и составные типы).

    Все операции выполняются кнопками (без ручного SQL).
    """

    def __init__(self, parent: QWidget | None = None, schema: str = "app") -> None:
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Пользовательские типы — менеджер")
        self.setMinimumSize(900, 560)

        # --- Валидаторы ---
        # Для имен, которые код будет заключать в двойные кавычки (f'"{name}"')
        # Запрещаем только сами двойные кавычки.
        self._name_validator =  QRegExpValidator(QRegExp(r'^[^"\'/\\|`=?!~+<>:;-]*$'))
        # Для значений, которые пользователь вводит без кавычек (e.g. 'draft', а не "'draft'")
        # Запрещаем одинарные кавычки, т.к. они сломают SQL или парсинг
        self._value_validator =  QRegExpValidator(QRegExp(r'^[^"\'/\\|`=?!~+<>:;-]*$'))
        # Для списков значений (запрещаем одинарные кавычки)
        self._value_list_validator =  QRegExpValidator(QRegExp(r'^[^"\'/\\|`=?!~+<>:;-]*$'))
        # --------------------

        self._current_oid: int | None = None
        self._current_kind: str | None = None  # 'e' or 'c'
        self._current_name: str | None = None

        self._build_ui()
        self._wire_actions()
        self._refresh_types()

    # --- UI ---
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Toolbar
        tb = QHBoxLayout()
        self.btnNewEnum = QPushButton("+ ENUM")
        self.btnNewComposite = QPushButton("+ Составной")
        self.btnRenameType = QPushButton("Переименовать тип…")
        self.btnDropType = QPushButton("Удалить тип…")
        self.btnRefresh = QPushButton("Обновить")
        tb.addWidget(self.btnNewEnum)
        tb.addWidget(self.btnNewComposite)
        tb.addStretch(1)
        tb.addWidget(self.btnRenameType)
        tb.addWidget(self.btnDropType)
        tb.addWidget(self.btnRefresh)
        root.addLayout(tb)

        # Splitter: list of types (left) and details (right)
        split = QSplitter()
        split.setOrientation(Qt.Horizontal)
        root.addWidget(split, 1)

        # Left pane — types list with filter/search
        left = QWidget();
        ll = QVBoxLayout(left)
        filt = QHBoxLayout()
        self.cbFilter = QComboBox();
        self.cbFilter.addItems(["ВСЕ", "ENUM", "Составные"])
        self.edSearch = QLineEdit();
        self.edSearch.setPlaceholderText("Поиск по имени…")
        filt.addWidget(QLabel("Фильтр:"))
        filt.addWidget(self.cbFilter)
        filt.addWidget(self.edSearch, 1)
        ll.addLayout(filt)

        self.listTypes = QListWidget()
        self.listTypes.setSelectionMode(QAbstractItemView.SingleSelection)
        ll.addWidget(self.listTypes, 1)
        split.addWidget(left)

        # Right pane — details
        right = QWidget();
        rl = QVBoxLayout(right)
        self.lblHeader = QLabel("")
        self.lblHeader.setStyleSheet("font-weight: bold; font-size: 16px;")
        rl.addWidget(self.lblHeader)

        # ENUM box
        self.boxEnum = QGroupBox("Значения ENUM")
        be = QVBoxLayout(self.boxEnum)
        self.tblEnum = QTableWidget(0, 1)
        self.tblEnum.setHorizontalHeaderLabels(["label"])
        self.tblEnum.verticalHeader().setVisible(False)
        self.tblEnum.setEditTriggers(QAbstractItemView.NoEditTriggers)
        be.addWidget(self.tblEnum, 1)

        enumBtns = QHBoxLayout()
        self.edNewEnumVal = QLineEdit();
        self.edNewEnumVal.setPlaceholderText("Новый label")
        self.edNewEnumVal.setValidator(self._value_validator)  # <-- Валидация
        self.cbPosRel = QComboBox()
        self.cbPosRel.addItems(["в конец", "ПЕРЕД…", "ПОСЛЕ…"])
        self.cbPosRef = QComboBox();  # values will be filled based on current list
        enumBtns.addWidget(self.edNewEnumVal, 2)
        enumBtns.addWidget(self.cbPosRel)
        enumBtns.addWidget(self.cbPosRef, 2)
        self.btnAddEnumVal = QPushButton("Добавить значение")
        enumBtns.addWidget(self.btnAddEnumVal)
        be.addLayout(enumBtns)
        rl.addWidget(self.boxEnum)

        # COMPOSITE box
        self.boxComposite = QGroupBox("Атрибуты составного типа")
        bc = QVBoxLayout(self.boxComposite)
        self.tblAttrs = QTableWidget(0, 3)
        self.tblAttrs.setHorizontalHeaderLabels(["Имя", "Тип", "Позиция"])
        self.tblAttrs.verticalHeader().setVisible(False)
        self.tblAttrs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tblAttrs.setSelectionBehavior(QAbstractItemView.SelectRows)
        bc.addWidget(self.tblAttrs, 1)

        compBtns = QHBoxLayout()
        self.btnAddAttr = QPushButton("+ Атрибут…")
        self.btnRenameAttr = QPushButton("Переименовать…")
        self.btnDropAttr = QPushButton("Удалить…")
        self.btnAlterAttrType = QPushButton("Изменить тип…")
        compBtns.addWidget(self.btnAddAttr)
        compBtns.addWidget(self.btnRenameAttr)
        compBtns.addWidget(self.btnDropAttr)
        compBtns.addWidget(self.btnAlterAttrType)
        bc.addLayout(compBtns)
        rl.addWidget(self.boxComposite)

        split.addWidget(right)
        split.setStretchFactor(1, 2)

        # Footer: helper
        foot = QHBoxLayout()
        self.lblUsage = QLabel("")
        self.btnCopyName = QPushButton("Скопировать имя типа")
        foot.addWidget(self.lblUsage, 1)
        foot.addWidget(self.btnCopyName)
        root.addLayout(foot)

        self._apply_styles()

    # ... (стили _apply_styles не изменились) ...
    def _apply_styles(self) -> None:
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
                            font-size: 18px;
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
                            font-size: 14px;
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
                            font-size: 18px;
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
                        QGroupBox {
                            color: white;
                            font-size: 18px;
                            font-weight: bold;
                            padding-top: 10px;
                        }
                        QGroupBox::title {
                            color: white;
                            subcontrol-origin: margin;
                            left: 10px;
                            padding: 0 5px 0 5px;
                        }
        """)

    # --- Wiring ---
    def _wire_actions(self) -> None:
        # ... (не изменилось) ...
        self.btnRefresh.clicked.connect(self._refresh_types)
        self.cbFilter.currentIndexChanged.connect(self._filter_changed)
        self.edSearch.textChanged.connect(self._apply_filter)
        self.listTypes.currentItemChanged.connect(self._on_type_selected)

        self.btnNewEnum.clicked.connect(self._on_new_enum)
        self.btnNewComposite.clicked.connect(self._on_new_composite)
        self.btnRenameType.clicked.connect(self._on_rename_type)
        self.btnDropType.clicked.connect(self._on_drop_type)
        self.btnCopyName.clicked.connect(self._copy_type_name)

        self.btnAddEnumVal.clicked.connect(self._on_add_enum_value)
        self.cbPosRel.currentIndexChanged.connect(self._on_pos_mode_changed)

        self.btnAddAttr.clicked.connect(self._on_add_attr)
        self.btnRenameAttr.clicked.connect(self._on_rename_attr)
        self.btnDropAttr.clicked.connect(self._on_drop_attr)
        self.btnAlterAttrType.clicked.connect(self._on_alter_attr_type)

    # ... (загрузка данных _refresh_types, _filter_changed, _apply_filter, _show_none, _on_type_selected не изменились) ...

    # --- Data loading & filtering ---
    def _refresh_types(self) -> None:
        try:
            self._all_types = list_user_defined_types(self.schema)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список типов: {e}")
            self._all_types = []
        self._apply_filter()

    def _filter_changed(self, *_):
        self._apply_filter()

    def _apply_filter(self) -> None:
        kind = self.cbFilter.currentText()
        q = (self.edSearch.text() or "").strip().lower()
        self.listTypes.clear()
        for t in self._all_types:
            if kind == "ENUM" and t["kind"] != 'e':
                continue
            if kind == "Составные" and t["kind"] != 'c':
                continue
            name = t["name"]
            if q and q not in name.lower():
                continue
            item = QListWidgetItem(f"{name}  ·  {'ENUM' if t['kind'] == 'e' else 'COMPOSITE'}")
            item.setData(Qt.UserRole, t)
            self.listTypes.addItem(item)
        if self.listTypes.count() > 0:
            self.listTypes.setCurrentRow(0)
        else:
            self._show_none()

    def _show_none(self) -> None:
        self._current_oid = None
        self._current_kind = None
        self._current_name = None
        self.lblHeader.setText("Нет выбранного типа")
        self.boxEnum.setVisible(False)
        self.boxComposite.setVisible(False)
        self.lblUsage.setText("")

    def _on_type_selected(self, item: QListWidgetItem | None) -> None:
        if not item:
            self._show_none();
            return
        meta = item.data(Qt.UserRole)
        self._current_oid = meta["oid"]
        self._current_kind = meta["kind"]
        self._current_name = meta["name"]
        fq = f'{self.schema}."{self._current_name}"'
        self.lblHeader.setText(f"Тип: {fq} — {'ENUM' if meta['kind'] == 'e' else 'COMPOSITE'}")
        self.lblUsage.setText(f"Использование (например в CREATE TABLE): {fq}")
        if meta['kind'] == 'e':
            self._load_enum_values()
        else:
            self._load_composite_attrs()

    # --- ENUM handling ---
    def _load_enum_values(self) -> None:
        # ... (не изменилось) ...
        self.boxComposite.setVisible(False)
        self.boxEnum.setVisible(True)
        self.tblEnum.setRowCount(0)
        self.cbPosRef.clear()
        labels = []
        try:
            labels = list_enum_labels(self._current_oid) if self._current_oid else []
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить значения ENUM: {e}")
        for i, lab in enumerate(labels):
            self.tblEnum.insertRow(i)
            self.tblEnum.setItem(i, 0, QTableWidgetItem(lab))
            self.cbPosRef.addItem(lab)
        self.cbPosRel.setCurrentIndex(0)  # "в конец"
        self._on_pos_mode_changed()

    def _on_pos_mode_changed(self):
        # ... (не изменилось) ...
        need_ref = self.cbPosRel.currentText() != "в конец"
        self.cbPosRef.setEnabled(need_ref)

    def _on_add_enum_value(self) -> None:
        # ... (не изменилось) ...
        if not self._current_name or self._current_kind != 'e':
            return
        label = (self.edNewEnumVal.text() or "").strip()
        if not label:
            QMessageBox.warning(self, "ENUM", "Укажите значение")
            return
        pos_clause = ""
        mode = self.cbPosRel.currentText()
        if mode == "ПЕРЕД…" and self.cbPosRef.currentText():
            pos_clause = f" BEFORE '{self.cbPosRef.currentText()}'"
        elif mode == "ПОСЛЕ…" and self.cbPosRef.currentText():
            pos_clause = f" AFTER '{self.cbPosRef.currentText()}'"
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" ADD VALUE IF NOT EXISTS %s{pos_clause}'
        try:
            db.exec_txn([(sql, (label,))])
            self.edNewEnumVal.clear()
            self._load_enum_values()
            QMessageBox.information(self, "ENUM", "Значение добавлено.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить значение: {e}")

    # --- COMPOSITE handling ---
    def _load_composite_attrs(self) -> None:
        # ... (не изменилось) ...
        self.boxEnum.setVisible(False)
        self.boxComposite.setVisible(True)
        self.tblAttrs.setRowCount(0)
        rows: List[Tuple[str, str, int]] = []
        try:
            rows = list_composite_attrs(self._current_oid) if self._current_oid else []
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить атрибуты: {e}")
        for i, (name, typ, pos) in enumerate(rows):
            self.tblAttrs.insertRow(i)
            self.tblAttrs.setItem(i, 0, QTableWidgetItem(name))
            self.tblAttrs.setItem(i, 1, QTableWidgetItem(typ))
            self.tblAttrs.setItem(i, 2, QTableWidgetItem(str(pos)))

    def _require_attr_row(self) -> Tuple[str, str] | None:
        # ... (не изменилось) ...
        r = self.tblAttrs.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Атрибут", "Выберите атрибут")
            return None
        name = self.tblAttrs.item(r, 0).text()
        typ = self.tblAttrs.item(r, 1).text()
        return name, typ

    def _on_add_attr(self) -> None:
        if not self._current_name or self._current_kind != 'c':
            return
        # Передаем валидатор в саб-диалог
        dlg = _AttrEditor(self, title="Добавить атрибут", allow_type=True, name_validator=self._name_validator)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, typ = dlg.name.text().strip(), dlg.typ.text().strip()
        if not name or not typ:
            return
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" ADD ATTRIBUTE "{name}" {typ}'
        try:
            db.exec_txn([(sql, ())])
            self._load_composite_attrs()
            QMessageBox.information(self, "OK", "Атрибут добавлен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить атрибут: {e}")

    def _on_rename_attr(self) -> None:
        need = self._require_attr_row()
        if not need:
            return
        old, _ = need
        # Передаем валидатор в саб-диалог
        dlg = _AttrEditor(self, title="Переименовать атрибут", allow_type=False, name_validator=self._name_validator)
        dlg.name.setText(old)
        if dlg.exec_() != QDialog.Accepted:
            return
        new = dlg.name.text().strip()
        if not new or new == old:
            return
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" RENAME ATTRIBUTE "{old}" TO "{new}"'
        try:
            db.exec_txn([(sql, ())])
            self._load_composite_attrs()
            QMessageBox.information(self, "OK", "Атрибут переименован.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать атрибут: {e}")

    def _on_drop_attr(self) -> None:
        # ... (не изменилось) ...
        need = self._require_attr_row()
        if not need:
            return
        name, _ = need
        if QMessageBox.question(self, "Удаление", f"Удалить атрибут \"{name}\"?") != QMessageBox.Yes:
            return
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" DROP ATTRIBUTE "{name}"'
        try:
            db.exec_txn([(sql, ())])
            self._load_composite_attrs()
            QMessageBox.information(self, "OK", "Атрибут удалён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить атрибут: {e}")

    def _on_alter_attr_type(self) -> None:
        # ... (не изменилось) ...
        need = self._require_attr_row()
        if not need:
            return
        name, old_typ = need
        dlg = _AttrEditor(self, title=f"Тип для {name}", allow_type=True)
        dlg.typ.setText(old_typ)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_typ = dlg.typ.text().strip()
        if not new_typ or new_typ == old_typ:
            return
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" ALTER ATTRIBUTE "{name}" TYPE {new_typ}'
        try:
            db.exec_txn([(sql, ())])
            self._load_composite_attrs()
            QMessageBox.information(self, "OK", "Тип атрибута изменён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось изменить тип атрибута: {e}")

    # --- Type-level actions ---
    def _on_new_enum(self) -> None:
        # Передаем валидаторы в саб-диалог
        dlg = _NewEnumDialog(self, schema=self.schema,
                             name_validator=self._name_validator,
                             value_list_validator=self._value_list_validator)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_types()

    def _on_new_composite(self) -> None:
        # Передаем валидаторы в саб-диалог
        dlg = _NewCompositeDialog(self, schema=self.schema,
                                  name_validator=self._name_validator,
                                  value_list_validator=self._value_list_validator)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_types()

    def _on_rename_type(self) -> None:
        if not self._current_name:
            return
        # Передаем валидатор в саб-диалог
        new, ok = _prompt_text(self, "Новое имя типа", self._current_name, validator=self._name_validator)
        if not ok or not new or new == self._current_name:
            return
        sql = f'ALTER TYPE {self.schema}."{self._current_name}" RENAME TO "{new}"'
        try:
            db.exec_txn([(sql, ())])
            self._refresh_types()
            QMessageBox.information(self, "OK", "Тип переименован.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать тип: {e}")

    def _on_drop_type(self) -> None:
        # ... (не изменилось) ...
        if not self._current_name:
            return
        if QMessageBox.question(self, "Удаление типа",
                                f"Удалить тип {self.schema}.\"{self._current_name}\"?\n\nВНИМАНИЕ: будет попытка CASCADE.") != QMessageBox.Yes:
            return
        sql = f'DROP TYPE {self.schema}."{self._current_name}" CASCADE'
        try:
            db.exec_txn([(sql, ())])
            self._refresh_types()
            QMessageBox.information(self, "OK", "Тип удалён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тип: {e}")

    def _copy_type_name(self) -> None:
        # ... (не изменилось) ...
        if not self._current_name:
            return
        fq = f'{self.schema}."{self._current_name}"'
        QApplication.clipboard().setText(fq)
        QMessageBox.information(self, "Имя скопировано", fq)


# --- Subdialogs ---

class _NewEnumDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, schema: str = "app",
                 name_validator: QRegExpValidator | None = None,
                 value_list_validator: QRegExpValidator | None = None) -> None:
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Создать ENUM")
        L = QVBoxLayout(self)

        form = QFormLayout()
        self.edName = QLineEdit()
        self.edName.setPlaceholderText("имя типа")
        if name_validator:
            self.edName.setValidator(name_validator)  # <-- Валидация

        self.edValues = QLineEdit()
        self.edValues.setPlaceholderText("значения через запятую, например: draft, active, archived")
        if value_list_validator:
            self.edValues.setValidator(value_list_validator)  # <-- Валидация

        form.addRow("Имя:", self.edName)
        form.addRow("Значения:", self.edValues)
        L.addLayout(form)

        hb = QHBoxLayout()
        ok = QPushButton("Создать")
        ok.clicked.connect(self._on_ok)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        hb.addStretch(1)
        hb.addWidget(ok)
        hb.addWidget(cancel)
        L.addLayout(hb)

    def _on_ok(self):
        # ... (логика не изменилась, т.к. валидатор не дает ввести плохие символы) ...
        name = (self.edName.text() or "").strip()
        vals = [v.strip() for v in (self.edValues.text() or "").split(',') if v.strip()]
        if not name:
            QMessageBox.warning(self, "ENUM", "Укажите имя типа")
            return
        if not vals:
            QMessageBox.warning(self, "ENUM", "Укажите хотя бы одно значение")
            return
        placeholders = ", ".join(["%s"] * len(vals))
        sql = f'CREATE TYPE {self.schema}."{name}" AS ENUM ({placeholders})'
        try:
            db.exec_txn([(sql, tuple(vals))])
            QMessageBox.information(self, "OK", "ENUM создан.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать ENUM: {e}")


class _NewCompositeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, schema: str = "app",
                 name_validator: QRegExpValidator | None = None,
                 value_list_validator: QRegExpValidator | None = None) -> None:
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Создать составной тип")
        L = QVBoxLayout(self)

        form = QFormLayout()
        self.edName = QLineEdit()
        self.edName.setPlaceholderText("имя типа")
        if name_validator:
            self.edName.setValidator(name_validator)  # <-- Валидация

        self.edAttrs = QLineEdit()
        self.edAttrs.setPlaceholderText("список атрибутов: name1 type1, name2 type2 …")
        # Атрибуты могут содержать сложные типы (e.g. text[]),
        # но как минимум запретим одинарные кавычки, которые там не нужны.
        if value_list_validator:
            self.edAttrs.setValidator(value_list_validator)  # <-- Валидация

        form.addRow("Имя:", self.edName)
        form.addRow("Атрибуты:", self.edAttrs)
        L.addLayout(form)

        tip = QLabel(
            "Пример: <code>street text, city text, zip integer</code>\n" \
            "Поддерживаются пользовательские типы: <code>profile_status</code>, массивы: <code>text[]</code>."
        )
        tip.setTextFormat(Qt.RichText)
        L.addWidget(tip)

        hb = QHBoxLayout()
        ok = QPushButton("Создать")
        ok.clicked.connect(self._on_ok)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        hb.addStretch(1)
        hb.addWidget(ok)
        hb.addWidget(cancel)
        L.addLayout(hb)

    def _on_ok(self):
        # ... (логика не изменилась) ...
        name = (self.edName.text() or "").strip()
        attrs_raw = (self.edAttrs.text() or "").strip().rstrip(',')
        if not name:
            QMessageBox.warning(self, "Составной тип", "Укажите имя типа")
            return
        if not attrs_raw:
            QMessageBox.warning(self, "Составной тип", "Укажите хотя бы один атрибут")
            return
        # На стороне сервера синтаксис уже проверится, здесь лишь базовая защита от пустых имён
        parts = [p.strip() for p in attrs_raw.split(',') if p.strip()]
        bad = [p for p in parts if ' ' not in p]
        if bad:
            QMessageBox.warning(self, "Составной тип", f"Неверный фрагмент: {bad[0]} (ожидается 'name type')")
            return
        sql = f'CREATE TYPE {self.schema}."{name}" AS ({attrs_raw})'
        try:
            db.exec_txn([(sql, ())])
            QMessageBox.information(self, "OK", "Составной тип создан.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать тип: {e}")


class _AttrEditor(QDialog):
    def __init__(self, parent: QWidget | None = None, title: str = "", allow_type: bool = True,
                 name_validator: QRegExpValidator | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title or "Атрибут")
        L = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit()
        self.typ = QLineEdit()
        if name_validator:
            self.name.setValidator(name_validator)  # <-- Валидация

        if allow_type:
            form.addRow("Тип:", self.typ)  # Тип не валидируем, т.к. он может быть сложным (varchar(100), text[], etc.)
        L.addLayout(form)
        hb = QHBoxLayout()
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        hb.addStretch(1);
        hb.addWidget(ok);
        hb.addWidget(cancel)
        L.addLayout(hb)


# --- Tiny helpers ---

def _prompt_text(parent: QWidget, title: str, initial: str = "",
                 validator: QRegExpValidator | None = None) -> Tuple[str, bool]:
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    L = QVBoxLayout(dlg)
    ed = QLineEdit()
    ed.setText(initial)
    if validator:
        ed.setValidator(validator)  # <-- Валидация
    L.addWidget(ed)
    hb = QHBoxLayout()
    ok = QPushButton("OK")
    cancel = QPushButton("Отмена")
    hb.addStretch(1)
    hb.addWidget(ok)
    hb.addWidget(cancel)
    L.addLayout(hb)
    ok.clicked.connect(dlg.accept)
    cancel.clicked.connect(dlg.reject)
    if dlg.exec_() == QDialog.Accepted:
        return ed.text(), True
    return "", False


# Public utility for other modules (e.g., to enrich type pickers)

def get_udt_names(schema: str = "app") -> List[str]:
    # ... (не изменилось) ...
    rows = list_user_defined_types(schema)
    return [r["name"] for r in rows]