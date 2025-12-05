from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QGroupBox, QWidget, QSplitter)
from PyQt5.QtCore import Qt
import db

class CTEBuilderDialog(QDialog):
    """
    Диалог для создания запросов с Common Table Expressions (CTE).
    
    Позволяет создавать множественные CTE через WITH-запросы
    и использовать их в главном запросе.
    """
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("CTE конструктор (WITH-запросы)")
        self.setMinimumSize(1600, 1000)
        
        # Применяем стили, аналогичные другим диалогам
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(16, 30, 41, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-size: 18px;
                padding: 6px;
            }
            QLineEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 8px;
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
                padding: 10px;
                min-height: 35px;
                min-width: 120px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(2, 65, 118, 200);
            }
            QGroupBox {
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-size: 16px;
                font-weight: bold;
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
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        main_layout.addWidget(QLabel("Конструктор Common Table Expressions (CTE)"))
        
        # Разделитель на две части: список CTE слева, редактор справа
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть: список CTE
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("Список CTE:"))
        self.cteList = QListWidget()
        self.cteList.itemSelectionChanged.connect(self._on_cte_selected)
        self.cteList.itemDoubleClicked.connect(self._edit_selected_cte)
        left_layout.addWidget(self.cteList, 1)
        
        # Кнопки управления CTE
        cte_buttons = QHBoxLayout()
        self.btnAddCTE = QPushButton("Добавить CTE")
        self.btnAddCTE.clicked.connect(self._add_cte)
        self.btnEditCTE = QPushButton("Редактировать")
        self.btnEditCTE.setEnabled(False)
        self.btnEditCTE.clicked.connect(self._edit_selected_cte)
        self.btnDeleteCTE = QPushButton("Удалить")
        self.btnDeleteCTE.setEnabled(False)
        self.btnDeleteCTE.clicked.connect(self._delete_selected_cte)
        self.btnMoveUp = QPushButton("↑")
        self.btnMoveUp.setEnabled(False)
        self.btnMoveUp.clicked.connect(self._move_cte_up)
        self.btnMoveDown = QPushButton("↓")
        self.btnMoveDown.setEnabled(False)
        self.btnMoveDown.clicked.connect(self._move_cte_down)
        
        cte_buttons.addWidget(self.btnAddCTE)
        cte_buttons.addWidget(self.btnEditCTE)
        cte_buttons.addWidget(self.btnDeleteCTE)
        cte_buttons.addWidget(self.btnMoveUp)
        cte_buttons.addWidget(self.btnMoveDown)
        left_layout.addLayout(cte_buttons)
        
        splitter.addWidget(left_widget)
        
        # Правая часть: редактор выбранного CTE и главный запрос
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Редактор выбранного CTE
        cte_editor_group = QGroupBox("Редактор CTE")
        cte_editor_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя CTE:"))
        self.edCTEName = QLineEdit()
        self.edCTEName.setPlaceholderText("Введите имя CTE (например: users_summary)")
        self.edCTEName.textChanged.connect(self._on_cte_name_changed)
        name_layout.addWidget(self.edCTEName, 1)
        cte_editor_layout.addLayout(name_layout)
        
        cte_editor_layout.addWidget(QLabel("SQL определение (SELECT запрос):"))
        self.edCTEDefinition = QTextEdit()
        self.edCTEDefinition.setPlaceholderText("Введите SELECT запрос или используйте SelectBuilder")
        self.edCTEDefinition.setMinimumHeight(200)
        cte_editor_layout.addWidget(self.edCTEDefinition, 1)
        
        # Кнопка для использования SelectBuilder
        btn_use_builder = QPushButton("Использовать SelectBuilder")
        btn_use_builder.clicked.connect(self._open_select_builder)
        cte_editor_layout.addWidget(btn_use_builder)
        
        # Кнопка сохранения изменений CTE
        self.btnSaveCTE = QPushButton("Сохранить изменения")
        self.btnSaveCTE.setEnabled(False)
        self.btnSaveCTE.clicked.connect(self._save_current_cte)
        cte_editor_layout.addWidget(self.btnSaveCTE)
        
        cte_editor_group.setLayout(cte_editor_layout)
        right_layout.addWidget(cte_editor_group)
        
        # Главный запрос
        main_query_group = QGroupBox("Главный запрос (использует CTE)")
        main_query_layout = QVBoxLayout()
        
        main_query_layout.addWidget(QLabel("Финальный SELECT запрос (может использовать CTE из списка):"))
        self.edMainQuery = QTextEdit()
        self.edMainQuery.setPlaceholderText("SELECT * FROM cte1 JOIN cte2 ON ...")
        self.edMainQuery.setMinimumHeight(150)
        main_query_layout.addWidget(self.edMainQuery, 1)
        
        # Кнопка для использования SelectBuilder для главного запроса
        btn_main_builder = QPushButton("Использовать SelectBuilder для главного запроса")
        btn_main_builder.clicked.connect(lambda: self._open_select_builder(self.edMainQuery))
        main_query_layout.addWidget(btn_main_builder)
        
        main_query_group.setLayout(main_query_layout)
        right_layout.addWidget(main_query_group)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter, 1)
        
        # Кнопки внизу
        bottom_buttons = QHBoxLayout()
        
        self.btnGenerateSQL = QPushButton("Сгенерировать SQL")
        self.btnGenerateSQL.clicked.connect(self._generate_sql)
        bottom_buttons.addWidget(self.btnGenerateSQL)
        
        self.btnExecute = QPushButton("Выполнить запрос")
        self.btnExecute.clicked.connect(self._execute_query)
        bottom_buttons.addWidget(self.btnExecute)
        
        bottom_buttons.addStretch()
        
        self.btnSaveAsView = QPushButton("Сохранить как VIEW")
        self.btnSaveAsView.clicked.connect(self._save_as_view)
        bottom_buttons.addWidget(self.btnSaveAsView)
        
        self.btnClose = QPushButton("Закрыть")
        self.btnClose.clicked.connect(self.accept)
        bottom_buttons.addWidget(self.btnClose)
        
        main_layout.addLayout(bottom_buttons)
        
        # Предпросмотр SQL
        preview_group = QGroupBox("Сгенерированный SQL")
        preview_layout = QVBoxLayout()
        self.sqlPreview = QTextEdit()
        self.sqlPreview.setReadOnly(True)
        self.sqlPreview.setMaximumHeight(200)
        preview_layout.addWidget(self.sqlPreview)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Таблица результатов
        results_group = QGroupBox("Результаты запроса")
        results_layout = QVBoxLayout()
        self.resultsTable = QTableWidget()
        results_layout.addWidget(self.resultsTable, 1)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group, 2)
        
        # Хранилище CTE: список словарей {name, definition}
        self.cte_data = []
        self.current_cte_index = -1
    
    def _add_cte(self):
        """Добавить новый CTE"""
        # Добавляем пустой CTE
        cte = {"name": "", "definition": ""}
        self.cte_data.append(cte)
        
        # Добавляем в список
        item = QListWidgetItem("Новый CTE")
        item.setData(Qt.UserRole, len(self.cte_data) - 1)
        self.cteList.addItem(item)
        
        # Выбираем новый CTE для редактирования
        self.cteList.setCurrentItem(item)
        self._on_cte_selected()
    
    def _on_cte_selected(self):
        """Обработчик выбора CTE из списка"""
        items = self.cteList.selectedItems()
        has_selection = len(items) > 0
        
        self.btnEditCTE.setEnabled(has_selection)
        self.btnDeleteCTE.setEnabled(has_selection)
        self.btnMoveUp.setEnabled(has_selection)
        self.btnMoveDown.setEnabled(has_selection)
        
        if has_selection:
            item = items[0]
            index = item.data(Qt.UserRole)
            self.current_cte_index = index
            
            if 0 <= index < len(self.cte_data):
                cte = self.cte_data[index]
                self.edCTEName.setText(cte["name"])
                self.edCTEDefinition.setPlainText(cte["definition"])
                self.btnSaveCTE.setEnabled(True)
        else:
            self.current_cte_index = -1
            self.edCTEName.clear()
            self.edCTEDefinition.clear()
            self.btnSaveCTE.setEnabled(False)
    
    def _on_cte_name_changed(self):
        """Обновить имя CTE в списке при изменении"""
        if self.current_cte_index >= 0:
            name = self.edCTEName.text().strip()
            if name:
                # Обновляем в данных
                self.cte_data[self.current_cte_index]["name"] = name
                # Обновляем в списке
                items = self.cteList.selectedItems()
                if items:
                    items[0].setText(name)
            else:
                items = self.cteList.selectedItems()
                if items:
                    items[0].setText("Новый CTE")
    
    def _save_current_cte(self):
        """Сохранить изменения текущего CTE"""
        if self.current_cte_index < 0:
            return
        
        name = self.edCTEName.text().strip()
        definition = self.edCTEDefinition.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя CTE")
            return
        
        if not definition:
            QMessageBox.warning(self, "Ошибка", "Введите SQL определение")
            return
        
        # Валидация имени
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            QMessageBox.warning(self, "Ошибка", "Имя CTE может содержать только буквы, цифры и подчеркивания")
            return
        
        # Проверка уникальности имени
        for i, cte in enumerate(self.cte_data):
            if i != self.current_cte_index and cte["name"] == name:
                QMessageBox.warning(self, "Ошибка", f"CTE с именем '{name}' уже существует")
                return
        
        # Сохраняем
        self.cte_data[self.current_cte_index]["name"] = name
        self.cte_data[self.current_cte_index]["definition"] = definition
        
        # Обновляем список
        items = self.cteList.selectedItems()
        if items:
            items[0].setText(name)
        
        QMessageBox.information(self, "Успех", f"CTE '{name}' сохранено")
    
    def _edit_selected_cte(self):
        """Редактировать выбранный CTE (просто фокус на редакторе)"""
        self._on_cte_selected()
    
    def _delete_selected_cte(self):
        """Удалить выбранный CTE"""
        items = self.cteList.selectedItems()
        if not items:
            return
        
        item = items[0]
        index = item.data(Qt.UserRole)
        
        ret = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить CTE '{self.cte_data[index]['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret == QMessageBox.Yes:
            # Удаляем из данных
            del self.cte_data[index]
            
            # Удаляем из списка
            row = self.cteList.row(item)
            self.cteList.takeItem(row)
            
            # Обновляем индексы в оставшихся элементах
            for i in range(self.cteList.count()):
                self.cteList.item(i).setData(Qt.UserRole, i)
            
            self.current_cte_index = -1
            self.edCTEName.clear()
            self.edCTEDefinition.clear()
    
    def _move_cte_up(self):
        """Переместить CTE вверх в списке"""
        items = self.cteList.selectedItems()
        if not items:
            return
        
        current_row = self.cteList.row(items[0])
        if current_row > 0:
            # Меняем местами в данных
            self.cte_data[current_row], self.cte_data[current_row - 1] = \
                self.cte_data[current_row - 1], self.cte_data[current_row]
            
            # Меняем местами в списке
            item = self.cteList.takeItem(current_row)
            self.cteList.insertItem(current_row - 1, item)
            self.cteList.setCurrentItem(item)
            
            # Обновляем индексы
            for i in range(self.cteList.count()):
                self.cteList.item(i).setData(Qt.UserRole, i)
    
    def _move_cte_down(self):
        """Переместить CTE вниз в списке"""
        items = self.cteList.selectedItems()
        if not items:
            return
        
        current_row = self.cteList.row(items[0])
        if current_row < self.cteList.count() - 1:
            # Меняем местами в данных
            self.cte_data[current_row], self.cte_data[current_row + 1] = \
                self.cte_data[current_row + 1], self.cte_data[current_row]
            
            # Меняем местами в списке
            item = self.cteList.takeItem(current_row)
            self.cteList.insertItem(current_row + 1, item)
            self.cteList.setCurrentItem(item)
            
            # Обновляем индексы
            for i in range(self.cteList.count()):
                self.cteList.item(i).setData(Qt.UserRole, i)
    
    def _open_select_builder(self, text_edit: QTextEdit):
        """Открыть SelectBuilder и вставить результат в текстовое поле"""
        from select_builder_dialog import SelectBuilderDialog
        
        builder = SelectBuilderDialog(self, schema=self.schema)
        if builder.exec_() == QDialog.Accepted:
            sql = builder.sqlView.toPlainText().strip()
            if sql:
                text_edit.setPlainText(sql)
    
    def _generate_sql(self):
        """Сгенерировать финальный SQL запрос с CTE"""
        # Проверяем, что все CTE имеют имя и определение
        for i, cte in enumerate(self.cte_data):
            if not cte["name"] or not cte["definition"]:
                QMessageBox.warning(self, "Ошибка", f"CTE #{i+1} не заполнено (нужны имя и определение)")
                return
        
        # Проверяем главный запрос
        main_query = self.edMainQuery.toPlainText().strip()
        if not main_query:
            QMessageBox.warning(self, "Ошибка", "Введите главный запрос")
            return
        
        # Генерируем SQL
        sql_parts = []
        
        if self.cte_data:
            # Формируем WITH часть
            with_parts = []
            for cte in self.cte_data:
                name = cte["name"]
                definition = cte["definition"]
                with_parts.append(f"{name} AS (\n{definition}\n)")
            
            sql_parts.append("WITH " + ",\n".join(with_parts))
        
        # Добавляем главный запрос
        sql_parts.append(main_query)
        
        final_sql = "\n".join(sql_parts)
        self.sqlPreview.setPlainText(final_sql)
    
    def _execute_query(self):
        """Выполнить сгенерированный SQL запрос"""
        sql = self.sqlPreview.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте SQL")
            return
        
        if not sql.upper().startswith("WITH") and not sql.upper().startswith("SELECT"):
            QMessageBox.warning(self, "Ошибка", "Разрешен только SELECT запрос")
            return
        
        try:
            cols, rows = db.preview(sql, limit=500)
            self.resultsTable.setColumnCount(len(cols))
            self.resultsTable.setHorizontalHeaderLabels(cols)
            self.resultsTable.setRowCount(len(rows))
            
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.resultsTable.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выполнении запроса:\n{e}")
    
    def _save_as_view(self):
        """Сохранить результат как VIEW"""
        sql = self.sqlPreview.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте SQL")
            return
        
        # Создаем простой диалог для ввода имени VIEW
        dialog = QDialog(self)
        dialog.setWindowTitle("Создать VIEW")
        dialog.setMinimumSize(400, 150)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Имя VIEW:"))
        
        ed_name = QLineEdit()
        ed_name.setPlaceholderText("Введите имя VIEW")
        layout.addWidget(ed_name)
        
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("Создать")
        btn_cancel = QPushButton("Отмена")
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        result = [False]
        
        def on_ok():
            name = ed_name.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите имя VIEW")
                return
            
            # Валидация имени
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                QMessageBox.warning(dialog, "Ошибка", "Имя VIEW может содержать только буквы, цифры и подчеркивания")
                return
            
            # Проверяем существование
            if db.view_exists(self.schema, name, materialized=False):
                ret = QMessageBox.question(
                    dialog, "Подтверждение",
                    f"VIEW {name} уже существует. Перезаписать?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if ret != QMessageBox.Yes:
                    return
                db.drop_view(self.schema, name, materialized=False)
            
            try:
                # VIEW может содержать WITH запрос, PostgreSQL это поддерживает
                db.create_view(self.schema, name, sql, materialized=False, with_data=True)
                QMessageBox.information(dialog, "Успех", f"VIEW {name} создано")
                result[0] = True
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при создании VIEW:\n{e}")
        
        btn_ok.clicked.connect(on_ok)
        btn_cancel.clicked.connect(dialog.reject)
        
        dialog.exec_()

