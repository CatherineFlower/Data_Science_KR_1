from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QCheckBox, QStackedWidget, QWidget
)
from PyQt5.QtCore import Qt
import db

ACTIONS = [
    "ADD COLUMN",
    "DROP COLUMN",
    "RENAME COLUMN",
    "ALTER COLUMN TYPE",
    "SET/DROP NOT NULL",
    "SET/DROP DEFAULT",
    "ADD CONSTRAINT",
    "DROP CONSTRAINT",
    "RENAME TABLE"
]

# Таблицы, которые нельзя переименовывать
FORBIDDEN_RENAME_TABLES = {
    "app_user",
    "tracked_domain",
    "domain_state_log",
    "metric_sample",
    "protected_column",
}

# Встроенные типы
PG_DOC_TYPES = [
    "smallint", "integer", "bigint",
    "decimal", "numeric", "real", "double precision",
    "smallserial", "serial", "bigserial",
    "money",
    "character varying", "varchar", "character", "char", "text",
    "varchar(255)", "char(1)", "numeric(10,2)",
    "bytea",
    "date",
    "time without time zone", "time with time zone",
    "timestamp without time zone", "timestamp with time zone",
    "interval",
    "boolean",
    "point", "line", "lseg", "box", "path", "polygon", "circle",
    "cidr", "inet", "macaddr", "macaddr8",
    "bit", "bit varying", "varbit",
    "tsvector", "tsquery",
    "uuid",
    "json", "jsonb",
    "xml",
    "int4range", "int8range", "numrange", "tsrange", "tstzrange", "daterange",
    "oid", "pg_lsn", "txid_snapshot"
]

class AlterTableDialog(QDialog):
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("ALTER TABLE — конструктор")
        self.setMinimumWidth(640)

        # кэш полного списка таблиц (для восстановления после режима RENAME TABLE)
        self._table_cache = []
        self._rename_filter_mode = False  # флаг: комбобокс отфильтрован для RENAME TABLE

        L = QVBoxLayout(self)

        # Выбор таблицы
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Таблица:"))
        self.cbTable = QComboBox()
        self._load_tables_into_combo()
        self.cbTable.currentIndexChanged.connect(self._reload_columns_and_constraints)
        hl.addWidget(self.cbTable, 1)
        L.addLayout(hl)

        # Действие
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel("Действие:"))
        self.cbAction = QComboBox()
        self.cbAction.addItems(ACTIONS)
        self.cbAction.currentTextChanged.connect(self._on_action_changed)
        hl2.addWidget(self.cbAction, 1)
        L.addLayout(hl2)

        # Стек форм
        self.stack = QStackedWidget()

        # ADD COLUMN
        w_add = QWidget(); la = QVBoxLayout(w_add)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Имя столбца:"))
        self.edAddName = QLineEdit()
        r1.addWidget(self.edAddName, 1)
        la.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Тип:"))
        self.cbType = QComboBox(); self.cbType.setEditable(False)
        self.cbType.addItems(PG_DOC_TYPES)
        r2.addWidget(self.cbType, 1)
        self.chkArray = QCheckBox("[]")
        self.chkArray.setToolTip("Сделать тип массивом (добавить []), например: integer[]")
        r2.addWidget(self.chkArray)
        la.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("DEFAULT (необяз.):"))
        self.edDefaultAdd = QLineEdit()
        r3.addWidget(self.edDefaultAdd, 1)
        la.addLayout(r3)

        self.chkAddNotNull = QCheckBox("NOT NULL")
        la.addWidget(self.chkAddNotNull)
        self.stack.addWidget(w_add)

        # DROP COLUMN
        w_drop = QWidget(); ld = QVBoxLayout(w_drop)
        r = QHBoxLayout()
        r.addWidget(QLabel("Столбец:"))
        self.cbDropCol = QComboBox()
        r.addWidget(self.cbDropCol, 1)
        ld.addLayout(r)
        self.stack.addWidget(w_drop)

        # RENAME COLUMN
        w_ren = QWidget(); lr = QVBoxLayout(w_ren)
        r = QHBoxLayout()
        r.addWidget(QLabel("Столбец:")); self.cbRenCol = QComboBox(); r.addWidget(self.cbRenCol, 1)
        lr.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel("Новое имя:")); self.edNewName = QLineEdit(); r.addWidget(self.edNewName, 1)
        lr.addLayout(r)
        self.stack.addWidget(w_ren)

        # ALTER COLUMN TYPE
        w_altertype = QWidget(); lat = QVBoxLayout(w_altertype)
        r = QHBoxLayout()
        r.addWidget(QLabel("Столбец:")); self.cbAlterTypeCol = QComboBox(); r.addWidget(self.cbAlterTypeCol, 1)
        lat.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel("Новый тип:"))
        self.cbNewType = QComboBox(); self.cbNewType.setEditable(False)
        self.cbNewType.addItems(PG_DOC_TYPES)
        r.addWidget(self.cbNewType, 1)
        self.chkArrayType = QCheckBox("[]")
        self.chkArrayType.setToolTip("Сделать тип массивом (добавить []), например: text[]")
        r.addWidget(self.chkArrayType)
        lat.addLayout(r)
        self.stack.addWidget(w_altertype)

        # SET/DROP NOT NULL
        w_nn = QWidget(); lnn = QVBoxLayout(w_nn)
        r = QHBoxLayout()
        r.addWidget(QLabel("Столбец:")); self.cbNNCol = QComboBox(); r.addWidget(self.cbNNCol, 1)
        lnn.addLayout(r)
        self.chkSetNN = QCheckBox("SET NOT NULL (если не отмечено — DROP NOT NULL)")
        lnn.addWidget(self.chkSetNN)
        self.stack.addWidget(w_nn)

        # SET/DROP DEFAULT
        w_def = QWidget(); ldef = QVBoxLayout(w_def)
        r = QHBoxLayout()
        r.addWidget(QLabel("Столбец:")); self.cbDefCol = QComboBox(); r.addWidget(self.cbDefCol, 1)
        ldef.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel("DEFAULT-выражение:")); self.edDefault = QLineEdit(); r.addWidget(self.edDefault, 1)
        ldef.addLayout(r)
        self.chkSetDef = QCheckBox("SET DEFAULT (если не отмечено — DROP DEFAULT)")
        ldef.addWidget(self.chkSetDef)
        self.stack.addWidget(w_def)

        # ADD CONSTRAINT
        w_addc = QWidget(); lac = QVBoxLayout(w_addc)
        r = QHBoxLayout()
        r.addWidget(QLabel("Имя:")); self.edCName = QLineEdit(); r.addWidget(self.edCName, 1)
        lac.addLayout(r)
        r = QHBoxLayout()
        r.addWidget(QLabel("Тело (например: UNIQUE(col), CHECK (...))"))
        lac.addLayout(r)
        self.edCBody = QLineEdit(); lac.addWidget(self.edCBody)
        self.stack.addWidget(w_addc)

        # DROP CONSTRAINT
        w_drpc = QWidget(); ldc = QVBoxLayout(w_drpc)
        r = QHBoxLayout()
        r.addWidget(QLabel("CONSTRAINT:")); self.cbCName = QComboBox(); r.addWidget(self.cbCName, 1)
        ldc.addLayout(r)
        self.stack.addWidget(w_drpc)

        # RENAME TABLE
        w_rentab = QWidget(); lrt = QVBoxLayout(w_rentab)
        r = QHBoxLayout()
        r.addWidget(QLabel("Новое имя таблицы:"))
        self.edNewTableName = QLineEdit()
        r.addWidget(self.edNewTableName, 1)
        lrt.addLayout(r)
        self.stack.addWidget(w_rentab)

        # Кнопки
        btnApply = QPushButton("Применить")
        btnApply.clicked.connect(self._apply)
        L.addWidget(self.stack)
        L.addWidget(btnApply, alignment=Qt.AlignRight)

        # Первичная загрузка
        self._reload_columns_and_constraints()
        self._on_action_changed(self.cbAction.currentText())

    # Служебные методы 

    def _load_tables_into_combo(self):
        """Загрузить список таблиц схемы в комбобокс и сохранить кэш полного списка."""
        self.cbTable.clear()
        try:
            rows = db.list_tables(self.schema)
        except Exception:
            rows = []
        names = [t[1] for t in rows]
        self.cbTable.addItems(names)
        self._table_cache = names[:]

    def _restrict_tables_for_rename(self):

        # Для режима RENAME TABLE: показываем только разрешённые к переименованию таблицы.

        self._rename_filter_mode = True
        allowed = [n for n in self._table_cache if n not in FORBIDDEN_RENAME_TABLES]

        self.cbTable.blockSignals(True)
        self.cbTable.clear()
        if allowed:
            self.cbTable.addItems(allowed)
            self.cbTable.setEnabled(True)
        else:
            self.cbTable.addItem("(нет доступных)")
            self.cbTable.setEnabled(False)
            QMessageBox.warning(
                self, "RENAME TABLE",
                "Нет таблиц, доступных к переименованию (запрещённые: app_user, tracked_domain, "
                "domain_state_log, metric_sample, protected_column)."
            )
        self.cbTable.blockSignals(False)

    def _restore_full_table_combo(self):
        # Восстановить полный список таблиц (выход из режима RENAME TABLE).
        if not self._rename_filter_mode:
            return
        self._rename_filter_mode = False
        self.cbTable.blockSignals(True)
        self.cbTable.clear()
        if not self._table_cache:
            self._load_tables_into_combo()
        else:
            self.cbTable.addItems(self._table_cache)
        self.cbTable.blockSignals(False)
        self.cbTable.setEnabled(True)

    def _reload_columns_and_constraints(self):
        # Заполнить выпадающие списки колонок и ограничений под текущую таблицу.
        table = self.cbTable.currentText()
        try:
            cols_info = db.list_columns(self.schema, table)
        except Exception:
            cols_info = []
        cols = [c["column_name"] for c in cols_info]

        # Фильтр «защищённых» колонок
        safe_cols = []
        for c in cols:
            try:
                if hasattr(db, "is_column_protected") and db.is_column_protected(self.schema, table, c):
                    continue
            except Exception:
                pass
            safe_cols.append(c)

        # Общие комбобоксы с колонками
        for cb in (self.cbDropCol, self.cbRenCol, self.cbNNCol, self.cbDefCol):
            cb.clear(); cb.addItems(safe_cols)

        # Для ALTER TYPE
        if hasattr(self, "cbAlterTypeCol"):
            self.cbAlterTypeCol.clear(); self.cbAlterTypeCol.addItems(safe_cols)

        # Ограничения
        try:
            cons = db.list_constraint_names(self.schema, table)
        except Exception:
            cons = []
        self.cbCName.clear(); self.cbCName.addItems(cons)

    def _on_action_changed(self, act: str):
        mapping = {
            "ADD COLUMN": 0,
            "DROP COLUMN": 1,
            "RENAME COLUMN": 2,
            "ALTER COLUMN TYPE": 3,
            "SET/DROP NOT NULL": 4,
            "SET/DROP DEFAULT": 5,
            "ADD CONSTRAINT": 6,
            "DROP CONSTRAINT": 7,
            "RENAME TABLE": 8
        }
        self.stack.setCurrentIndex(mapping.get(act, 0))

        # Специальная логика для RENAME TABLE - фильтруем таблицы
        if act == "RENAME TABLE":
            self._restrict_tables_for_rename()
        else:
            self._restore_full_table_combo()

        # Сброс полей текущего действия
        self.edAddName.clear(); self.edDefaultAdd.clear(); self.chkAddNotNull.setChecked(False)
        if hasattr(self, "chkArray"): self.chkArray.setChecked(False)
        self.edNewName.clear(); self.chkSetNN.setChecked(False)
        self.edDefault.clear(); self.chkSetDef.setChecked(False)
        self.edCName.clear(); self.edCBody.clear()
        if hasattr(self, "chkArrayType"): self.chkArrayType.setChecked(False)
        if hasattr(self, "edNewTableName"): self.edNewTableName.clear()

    def _apply(self):
        s = self.schema
        t = self.cbTable.currentText()
        full = f'{s}."{t}"'
        act = self.cbAction.currentText()
        stmts = []

        try:
            if act == "ADD COLUMN":
                name = self.edAddName.text().strip()
                typ = self.cbType.currentText().strip()
                if getattr(self, "chkArray", None) and self.chkArray.isChecked():
                    typ = f"{typ}[]"
                if not name:
                    raise ValueError("Укажите имя столбца")
                if not typ:
                    raise ValueError("Выберите тип")
                expr = f'ALTER TABLE {full} ADD COLUMN "{name}" {typ}'
                if self.chkAddNotNull.isChecked():
                    expr += " NOT NULL"
                if self.edDefaultAdd.text().strip():
                    expr += " DEFAULT " + self.edDefaultAdd.text().strip()
                stmts.append((expr, ()))

            elif act == "DROP COLUMN":
                col = self.cbDropCol.currentText()
                if not col:
                    raise ValueError("Выберите столбец")
                stmts.append((f'ALTER TABLE {full} DROP COLUMN "{col}"', ()))

            elif act == "RENAME COLUMN":
                col = self.cbRenCol.currentText()
                new = self.edNewName.text().strip()
                if not col:
                    raise ValueError("Выберите столбец")
                if not new:
                    raise ValueError("Укажите новое имя")
                stmts.append((f'ALTER TABLE {full} RENAME COLUMN "{col}" TO "{new}"', ()))

            elif act == "ALTER COLUMN TYPE":
                col = self.cbAlterTypeCol.currentText().strip()
                newt = self.cbNewType.currentText().strip()
                if getattr(self, "chkArrayType", None) and self.chkArrayType.isChecked():
                    newt = f"{newt}[]"
                if not col:
                    raise ValueError("Выберите столбец")
                if not newt:
                    raise ValueError("Выберите новый тип")
                stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" TYPE {newt}', ()))

            elif act == "SET/DROP NOT NULL":
                col = self.cbNNCol.currentText()
                if not col:
                    raise ValueError("Выберите столбец")
                if self.chkSetNN.isChecked():
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" SET NOT NULL', ()))
                else:
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" DROP NOT NULL', ()))

            elif act == "SET/DROP DEFAULT":
                col = self.cbDefCol.currentText()
                if not col:
                    raise ValueError("Выберите столбец")
                if self.chkSetDef.isChecked():
                    expr = self.edDefault.text().strip()
                    if not expr:
                        raise ValueError("Укажите DEFAULT-выражение")
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" SET DEFAULT {expr}', ()))
                else:
                    stmts.append((f'ALTER TABLE {full} ALTER COLUMN "{col}" DROP DEFAULT', ()))

            elif act == "ADD CONSTRAINT":
                name = self.edCName.text().strip()
                body = self.edCBody.text().strip()
                if not name or not body:
                    raise ValueError("Укажите имя и тело ограничения")
                stmts.append((f'ALTER TABLE {full} ADD CONSTRAINT "{name}" {body}', ()))

            elif act == "DROP CONSTRAINT":
                name = self.cbCName.currentText()
                if not name:
                    raise ValueError("Выберите ограничение")
                stmts.append((f'ALTER TABLE {full} DROP CONSTRAINT "{name}"', ()))

            elif act == "RENAME TABLE":
                if not self.cbTable.isEnabled() or t == "(нет доступных)":
                    raise ValueError("Нет таблиц, доступных к переименованию.")
                # Запретить переименование запрещённых таблиц
                if t in FORBIDDEN_RENAME_TABLES:
                    raise ValueError(f'Таблица "{t}" является системно защищённой и не может быть переименована.')
                newt = self.edNewTableName.text().strip()
                if not newt:
                    raise ValueError("Укажите новое имя таблицы")
                stmts.append((f'ALTER TABLE {full} RENAME TO "{newt}"', ()))

            else:
                raise ValueError("Неизвестное действие")

            db.exec_txn(stmts)
            QMessageBox.information(self, "OK", "Изменения применены.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка ALTER TABLE", str(e))
