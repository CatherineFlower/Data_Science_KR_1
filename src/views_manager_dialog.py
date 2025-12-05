from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
                             QCheckBox, QTabWidget, QWidget, QGroupBox)
from PyQt5.QtCore import Qt
import db

class ViewsManagerDialog(QDialog):
    """
    Диалог для управления представлениями (VIEW и MATERIALIZED VIEW).
    
    Позволяет:
    - Просматривать список всех представлений
    - Просматривать структуру и данные представлений
    - Создавать новые представления
    - Редактировать существующие представления
    - Удалять представления
    - Обновлять MATERIALIZED VIEW
    """
    def __init__(self, parent=None, schema="app"):
        super().__init__(parent)
        self.schema = schema
        self.setWindowTitle("Управление представлениями")
        self.setMinimumSize(1400, 900)
        
        # Применяем стили, аналогичные другим диалогам проекта
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
            QComboBox {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 10px;
                min-height: 35px;
                font-size: 18px;
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
            }
            QLineEdit {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                border: 1px solid rgba(46, 82, 110, 255);
                border-radius: 4px;
                padding: 8px;
                font-size: 18px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(66, 122, 160, 255);
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
            QTextEdit:focus {
                border: 1px solid rgba(66, 122, 160, 255);
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
            QPushButton:pressed {
                background-color: rgba(2, 65, 118, 100);
            }
            QTabWidget::pane {
                border: 1px solid rgba(46, 82, 110, 255);
                background-color: rgba(16, 30, 41, 240);
            }
            QTabBar::tab {
                background-color: rgba(25, 45, 60, 200);
                color: white;
                padding: 10px 20px;
                border: 1px solid rgba(46, 82, 110, 255);
            }
            QTabBar::tab:selected {
                background-color: rgba(2, 65, 118, 255);
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
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Создаем основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок и выбор схемы
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Схема:"))
        self.cbSchema = QComboBox()
        self.cbSchema.addItem("app")
        self.cbSchema.currentTextChanged.connect(self._on_schema_changed)
        header_layout.addWidget(self.cbSchema, 1)
        
        # Кнопка обновления списка
        self.btnRefresh = QPushButton("Обновить список")
        self.btnRefresh.clicked.connect(self._refresh_views_list)
        header_layout.addWidget(self.btnRefresh)
        
        main_layout.addLayout(header_layout)
        
        # Создаем вкладки для разделения обычных и материализованных представлений
        self.tabs = QTabWidget()
        
        # Вкладка: Обычные VIEW
        self.tab_regular = QWidget()
        self._setup_regular_views_tab()
        self.tabs.addTab(self.tab_regular, "Обычные VIEW")
        
        # Вкладка: MATERIALIZED VIEW
        self.tab_materialized = QWidget()
        self._setup_materialized_views_tab()
        self.tabs.addTab(self.tab_materialized, "MATERIALIZED VIEW")
        
        main_layout.addWidget(self.tabs)
        
        # Кнопки управления внизу
        buttons_layout = QHBoxLayout()
        
        self.btnCreateView = QPushButton("Создать VIEW")
        self.btnCreateView.clicked.connect(self._create_view)
        buttons_layout.addWidget(self.btnCreateView)
        
        self.btnCreateMatView = QPushButton("Создать MATERIALIZED VIEW")
        self.btnCreateMatView.clicked.connect(self._create_materialized_view)
        buttons_layout.addWidget(self.btnCreateMatView)
        
        buttons_layout.addStretch()
        
        self.btnClose = QPushButton("Закрыть")
        self.btnClose.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btnClose)
        
        main_layout.addLayout(buttons_layout)
        
        # Загружаем список представлений при открытии
        self._refresh_views_list()
    
    def _setup_regular_views_tab(self):
        """Настройка вкладки для обычных VIEW"""
        layout = QVBoxLayout(self.tab_regular)
        layout.setSpacing(10)
        
        # Список представлений
        layout.addWidget(QLabel("Список представлений:"))
        self.listRegularViews = QListWidget()
        self.listRegularViews.itemDoubleClicked.connect(self._view_definition)
        self.listRegularViews.itemSelectionChanged.connect(self._on_regular_view_selected)
        layout.addWidget(self.listRegularViews, 2)
        
        # Кнопки управления выбранным представлением
        buttons_group = QGroupBox("Действия с выбранным представлением")
        buttons_layout = QHBoxLayout()
        
        self.btnViewDef = QPushButton("Просмотреть определение")
        self.btnViewDef.clicked.connect(self._view_definition)
        self.btnViewDef.setEnabled(False)
        buttons_layout.addWidget(self.btnViewDef)
        
        self.btnViewData = QPushButton("Просмотреть данные")
        self.btnViewData.clicked.connect(self._view_data)
        self.btnViewData.setEnabled(False)
        buttons_layout.addWidget(self.btnViewData)
        
        self.btnEditView = QPushButton("Редактировать")
        self.btnEditView.clicked.connect(self._edit_view)
        self.btnEditView.setEnabled(False)
        buttons_layout.addWidget(self.btnEditView)
        
        self.btnDeleteView = QPushButton("Удалить")
        self.btnDeleteView.clicked.connect(self._delete_view)
        self.btnDeleteView.setEnabled(False)
        buttons_layout.addWidget(self.btnDeleteView)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
    
    def _setup_materialized_views_tab(self):
        """Настройка вкладки для MATERIALIZED VIEW"""
        layout = QVBoxLayout(self.tab_materialized)
        layout.setSpacing(10)
        
        # Список материализованных представлений
        layout.addWidget(QLabel("Список материализованных представлений:"))
        self.listMatViews = QListWidget()
        self.listMatViews.itemDoubleClicked.connect(self._view_definition)
        self.listMatViews.itemSelectionChanged.connect(self._on_materialized_view_selected)
        layout.addWidget(self.listMatViews, 2)
        
        # Кнопки управления выбранным представлением
        buttons_group = QGroupBox("Действия с выбранным представлением")
        buttons_layout = QHBoxLayout()
        
        self.btnViewMatDef = QPushButton("Просмотреть определение")
        self.btnViewMatDef.clicked.connect(self._view_definition)
        self.btnViewMatDef.setEnabled(False)
        buttons_layout.addWidget(self.btnViewMatDef)
        
        self.btnViewMatData = QPushButton("Просмотреть данные")
        self.btnViewMatData.clicked.connect(self._view_data)
        self.btnViewMatData.setEnabled(False)
        buttons_layout.addWidget(self.btnViewMatData)
        
        self.btnRefreshMat = QPushButton("Обновить (REFRESH)")
        self.btnRefreshMat.clicked.connect(self._refresh_materialized_view)
        self.btnRefreshMat.setEnabled(False)
        buttons_layout.addWidget(self.btnRefreshMat)
        
        self.btnRefreshMatConcurrent = QPushButton("Обновить (CONCURRENTLY)")
        self.btnRefreshMatConcurrent.clicked.connect(self._refresh_materialized_view_concurrent)
        self.btnRefreshMatConcurrent.setEnabled(False)
        buttons_layout.addWidget(self.btnRefreshMatConcurrent)
        
        self.btnDeleteMatView = QPushButton("Удалить")
        self.btnDeleteMatView.clicked.connect(self._delete_view)
        self.btnDeleteMatView.setEnabled(False)
        buttons_layout.addWidget(self.btnDeleteMatView)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        # Информация о выбранном MATERIALIZED VIEW
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()
        self.lblMatViewInfo = QLabel("Выберите представление для просмотра информации")
        self.lblMatViewInfo.setWordWrap(True)
        info_layout.addWidget(self.lblMatViewInfo)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
    
    def _on_schema_changed(self):
        """Обработчик смены схемы - обновляем список представлений"""
        self.schema = self.cbSchema.currentText()
        self._refresh_views_list()
    
    def _refresh_views_list(self):
        """Обновить список всех представлений"""
        try:
            # Получаем список обычных VIEW
            regular_views = db.list_views(self.schema, materialized=False)
            self.listRegularViews.clear()
            for view in regular_views:
                item = QListWidgetItem(view['view_name'])
                item.setData(Qt.UserRole, view)
                self.listRegularViews.addItem(item)
            
            # Получаем список MATERIALIZED VIEW
            materialized_views = db.list_views(self.schema, materialized=True)
            self.listMatViews.clear()
            for view in materialized_views:
                # Формируем текст с информацией о размере
                text = view['view_name']
                if view.get('size'):
                    text += f" ({view['size']})"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, view)
                self.listMatViews.addItem(item)
            
            # Обновляем информацию, если есть выбранное представление
            self._on_materialized_view_selected()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список представлений:\n{e}")
    
    def _on_regular_view_selected(self):
        """Обработчик выбора обычного VIEW - активируем кнопки"""
        has_selection = len(self.listRegularViews.selectedItems()) > 0
        self.btnViewDef.setEnabled(has_selection)
        self.btnViewData.setEnabled(has_selection)
        self.btnEditView.setEnabled(has_selection)
        self.btnDeleteView.setEnabled(has_selection)
    
    def _on_materialized_view_selected(self):
        """Обработчик выбора MATERIALIZED VIEW - активируем кнопки и показываем информацию"""
        items = self.listMatViews.selectedItems()
        has_selection = len(items) > 0
        
        self.btnViewMatDef.setEnabled(has_selection)
        self.btnViewMatData.setEnabled(has_selection)
        self.btnRefreshMat.setEnabled(has_selection)
        self.btnRefreshMatConcurrent.setEnabled(has_selection)
        self.btnDeleteMatView.setEnabled(has_selection)
        
        # Показываем информацию о выбранном представлении
        if has_selection:
            item = items[0]
            view_data = item.data(Qt.UserRole)
            view_name = view_data['view_name']
            
            try:
                info = db.get_materialized_view_info(self.schema, view_name)
                if info:
                    info_text = f"<b>Имя:</b> {info['view_name']}<br>"
                    info_text += f"<b>Общий размер:</b> {info['total_size']}<br>"
                    info_text += f"<b>Размер данных:</b> {info['table_size']}<br>"
                    info_text += f"<b>Количество индексов:</b> {info['index_count']}<br>"
                    if info.get('comment'):
                        info_text += f"<b>Комментарий:</b> {info['comment']}"
                    self.lblMatViewInfo.setText(info_text)
                else:
                    self.lblMatViewInfo.setText(f"Информация о {view_name} недоступна")
            except Exception as e:
                self.lblMatViewInfo.setText(f"Ошибка получения информации: {e}")
        else:
            self.lblMatViewInfo.setText("Выберите представление для просмотра информации")
    
    def _get_selected_view_name(self, materialized: bool = False):
        """Получить имя выбранного представления"""
        if materialized:
            items = self.listMatViews.selectedItems()
        else:
            items = self.listRegularViews.selectedItems()
        
        if not items:
            return None
        
        item = items[0]
        view_data = item.data(Qt.UserRole)
        return view_data['view_name']
    
    def _view_definition(self):
        """Просмотр определения представления"""
        # Определяем, какая вкладка активна
        is_materialized = self.tabs.currentIndex() == 1
        view_name = self._get_selected_view_name(materialized=is_materialized)
        
        if not view_name:
            QMessageBox.warning(self, "Выбор", "Выберите представление для просмотра")
            return
        
        try:
            definition = db.get_view_definition(self.schema, view_name, materialized=is_materialized)
            if definition:
                # Создаем диалог для отображения определения
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Определение: {view_name}")
                dialog.setMinimumSize(800, 600)
                dialog.setStyleSheet(self.styleSheet())
                
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel(f"SQL определение представления <b>{self.schema}.{view_name}</b>:"))
                
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlainText(definition)
                layout.addWidget(text_edit)
                
                btn_close = QPushButton("Закрыть")
                btn_close.clicked.connect(dialog.accept)
                layout.addWidget(btn_close)
                
                dialog.exec_()
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось получить определение для {view_name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении определения:\n{e}")
    
    def _view_data(self):
        """Просмотр данных представления"""
        is_materialized = self.tabs.currentIndex() == 1
        view_name = self._get_selected_view_name(materialized=is_materialized)
        
        if not view_name:
            QMessageBox.warning(self, "Выбор", "Выберите представление для просмотра")
            return
        
        try:
            # Выполняем SELECT * FROM view с ограничением
            sql = f'SELECT * FROM {self.schema}."{view_name}" LIMIT 500'
            cols, rows = db.preview(sql, limit=500)
            
            # Создаем диалог для отображения данных
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Данные: {view_name}")
            dialog.setMinimumSize(1000, 700)
            dialog.setStyleSheet(self.styleSheet())
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel(f"Данные представления <b>{self.schema}.{view_name}</b> (показано до 500 строк):"))
            
            table = QTableWidget()
            table.setColumnCount(len(cols))
            table.setHorizontalHeaderLabels(cols)
            table.setRowCount(len(rows))
            
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
            
            layout.addWidget(table)
            
            btn_close = QPushButton("Закрыть")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при просмотре данных:\n{e}")
    
    def _edit_view(self):
        """Редактирование представления"""
        is_materialized = self.tabs.currentIndex() == 1
        view_name = self._get_selected_view_name(materialized=is_materialized)
        
        if not view_name:
            QMessageBox.warning(self, "Выбор", "Выберите представление для редактирования")
            return
        
        try:
            # Получаем текущее определение
            definition = db.get_view_definition(self.schema, view_name, materialized=is_materialized)
            if not definition:
                QMessageBox.warning(self, "Ошибка", f"Не удалось получить определение для {view_name}")
                return
            
            # Открываем диалог редактирования
            if self._create_edit_dialog(view_name, definition, is_materialized, is_edit=True):
                self._refresh_views_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании:\n{e}")
    
    def _delete_view(self):
        """Удаление представления"""
        is_materialized = self.tabs.currentIndex() == 1
        view_name = self._get_selected_view_name(materialized=is_materialized)
        
        if not view_name:
            QMessageBox.warning(self, "Выбор", "Выберите представление для удаления")
            return
        
        view_type = "MATERIALIZED VIEW" if is_materialized else "VIEW"
        ret = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Удалить {view_type} {self.schema}.{view_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if ret != QMessageBox.Yes:
            return
        
        try:
            db.drop_view(self.schema, view_name, materialized=is_materialized, cascade=False)
            QMessageBox.information(self, "Успех", f"{view_type} {view_name} удалено")
            self._refresh_views_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении:\n{e}")
    
    def _refresh_materialized_view(self):
        """Обновить MATERIALIZED VIEW обычным способом"""
        view_name = self._get_selected_view_name(materialized=True)
        if not view_name:
            return
        
        try:
            db.refresh_materialized_view(self.schema, view_name, concurrently=False)
            QMessageBox.information(self, "Успех", f"MATERIALIZED VIEW {view_name} обновлено")
            self._refresh_views_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении:\n{e}")
    
    def _refresh_materialized_view_concurrent(self):
        """Обновить MATERIALIZED VIEW с CONCURRENTLY"""
        view_name = self._get_selected_view_name(materialized=True)
        if not view_name:
            return
        
        try:
            db.refresh_materialized_view(self.schema, view_name, concurrently=True)
            QMessageBox.information(self, "Успех", f"MATERIALIZED VIEW {view_name} обновлено (CONCURRENTLY)")
            self._refresh_views_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении:\n{e}")
    
    def _create_view(self):
        """Создание нового обычного VIEW"""
        self._create_edit_dialog("", "", materialized=False, is_edit=False)
        self._refresh_views_list()
    
    def _create_materialized_view(self):
        """Создание нового MATERIALIZED VIEW"""
        self._create_edit_dialog("", "", materialized=True, is_edit=False)
        self._refresh_views_list()
    
    def _create_edit_dialog(self, view_name: str, definition: str, materialized: bool, is_edit: bool):
        """
        Диалог создания или редактирования представления
        
        Args:
            view_name: имя представления (пустое для создания)
            definition: SQL определение (пустое для создания)
            materialized: True для MATERIALIZED VIEW
            is_edit: True для редактирования, False для создания
        
        Returns:
            True если представление создано/изменено, False если отменено
        """
        dialog = QDialog(self)
        view_type = "MATERIALIZED VIEW" if materialized else "VIEW"
        dialog.setWindowTitle(f"{'Редактировать' if is_edit else 'Создать'} {view_type}")
        dialog.setMinimumSize(1000, 700)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        
        # Имя представления
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя представления:"))
        ed_name = QLineEdit()
        ed_name.setText(view_name)
        ed_name.setEnabled(not is_edit)  # При редактировании имя нельзя менять
        name_layout.addWidget(ed_name, 1)
        layout.addLayout(name_layout)
        
        # SQL определение
        layout.addWidget(QLabel("SQL определение (SELECT запрос):"))
        ed_definition = QTextEdit()
        ed_definition.setPlainText(definition)
        ed_definition.setMinimumHeight(300)
        layout.addWidget(ed_definition, 1)
        
        # Для MATERIALIZED VIEW - опция WITH DATA
        cb_with_data = None
        if materialized:
            cb_with_data = QCheckBox("WITH DATA (загрузить данные сразу)")
            cb_with_data.setChecked(True)
            layout.addWidget(cb_with_data)
        
        # Кнопка "Использовать SelectBuilder"
        btn_use_builder = QPushButton("Использовать SelectBuilder для создания запроса")
        btn_use_builder.clicked.connect(lambda: self._open_select_builder(ed_definition))
        layout.addWidget(btn_use_builder)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_save = QPushButton("Сохранить" if is_edit else "Создать")
        btn_cancel = QPushButton("Отмена")
        
        def on_save():
            name = ed_name.text().strip()
            def_text = ed_definition.toPlainText().strip()
            
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите имя представления")
                return
            
            if not def_text:
                QMessageBox.warning(dialog, "Ошибка", "Введите SQL определение")
                return
            
            # Валидация имени (только буквы, цифры, подчеркивания)
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                QMessageBox.warning(dialog, "Ошибка", "Имя представления может содержать только буквы, цифры и подчеркивания, и должно начинаться с буквы или подчеркивания")
                return
            
            try:
                with_data = cb_with_data.isChecked() if cb_with_data else True
                
                if is_edit:
                    # Для редактирования: удаляем старое и создаем новое с тем же именем
                    # (PostgreSQL не поддерживает CREATE OR REPLACE для всех типов VIEW)
                    db.drop_view(self.schema, view_name, materialized=materialized, cascade=False)
                    db.create_view(self.schema, name, def_text, materialized=materialized, with_data=with_data)
                    QMessageBox.information(dialog, "Успех", f"{view_type} {name} обновлено")
                else:
                    # При создании проверяем, не существует ли уже представление с таким именем
                    if db.view_exists(self.schema, name, materialized=materialized):
                        QMessageBox.warning(dialog, "Ошибка", f"{view_type} с именем {name} уже существует")
                        return
                    db.create_view(self.schema, name, def_text, materialized=materialized, with_data=with_data)
                    QMessageBox.information(dialog, "Успех", f"{view_type} {name} создано")
                
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при сохранении:\n{e}")
        
        btn_save.clicked.connect(on_save)
        btn_cancel.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(btn_save)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        return dialog.exec_() == QDialog.Accepted
    
    def _open_select_builder(self, text_edit: QTextEdit):
        """Открыть SelectBuilder и вставить результат в текстовое поле"""
        from select_builder_dialog import SelectBuilderDialog
        
        builder = SelectBuilderDialog(self, schema=self.schema)
        # Показываем диалог, пользователь может сгенерировать SQL и нажать "Сгенерировать SQL"
        if builder.exec_() == QDialog.Accepted:
            # Получаем сгенерированный SQL из SelectBuilder
            # SelectBuilder генерирует полный SELECT запрос, который можно использовать в VIEW
            sql = builder.sqlView.toPlainText().strip()
            if sql:
                text_edit.setPlainText(sql)
            else:
                QMessageBox.warning(self, "Предупреждение", "SQL не был сгенерирован. Нажмите 'Сгенерировать SQL' в SelectBuilder")

