# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1200, 800)

        # Фон окна как в MainMenu.py
        Form.setStyleSheet("background-color: rgba(16, 30, 41, 240);")

        # Главный вертикальный layout
        self.verticalLayout_main = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_main.setObjectName("verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout_main.setSpacing(10)

        # ЗАГОЛОВОК
        self.title_label = QtWidgets.QLabel(Form)
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
                background-color: rgba(2, 65, 118, 255);
                border-radius: 5px;
            }
        """)
        self.title_label.setMinimumHeight(60)
        self.verticalLayout_main.addWidget(self.title_label)

        # КОНТЕЙНЕР ДЛЯ КНОПОК
        self.buttons_container = QtWidgets.QWidget(Form)
        self.buttons_container.setObjectName("buttons_container")
        self.buttons_container.setMinimumHeight(100)
        self.buttons_container.setStyleSheet("background-color: transparent;")

        # Используем сетку для расположения кнопок
        self.gridLayout_buttons = QtWidgets.QGridLayout(self.buttons_container)
        self.gridLayout_buttons.setObjectName("gridLayout_buttons")
        self.gridLayout_buttons.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_buttons.setSpacing(10)
        self.gridLayout_buttons.setVerticalSpacing(10)

        # Стиль кнопок как в MainMenu.py
        button_style = """
            QPushButton {
                background-color: rgba(2, 65, 118, 255);
                color: rgba(255, 255, 255, 200);
                border-radius: 5px;
                padding: 10px;
                min-height: 40px;
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
        """

        # Создаем кнопки и размещаем их в сетке 2x4
        self.createSchemaButton = QtWidgets.QPushButton(self.buttons_container)
        self.createSchemaButton.setMinimumSize(QtCore.QSize(0, 40))
        self.createSchemaButton.setStyleSheet(button_style)
        self.createSchemaButton.setObjectName("createSchemaButton")
        self.gridLayout_buttons.addWidget(self.createSchemaButton, 0, 0)

        self.deleteSchemaButton = QtWidgets.QPushButton(self.buttons_container)
        self.deleteSchemaButton.setMinimumSize(QtCore.QSize(0, 40))
        self.deleteSchemaButton.setStyleSheet(button_style)
        self.deleteSchemaButton.setObjectName("deleteSchemaButton")
        self.gridLayout_buttons.addWidget(self.deleteSchemaButton, 0, 1)

        self.btnAlterTable = QtWidgets.QPushButton(self.buttons_container)
        self.btnAlterTable.setMinimumSize(QtCore.QSize(0, 40))
        self.btnAlterTable.setStyleSheet(button_style)
        self.btnAlterTable.setObjectName("btnAlterTable")
        self.gridLayout_buttons.addWidget(self.btnAlterTable, 0, 2)

        self.btnSelect = QtWidgets.QPushButton(self.buttons_container)
        self.btnSelect.setMinimumSize(QtCore.QSize(0, 40))
        self.btnSelect.setStyleSheet(button_style)
        self.btnSelect.setObjectName("btnSelect")
        self.gridLayout_buttons.addWidget(self.btnSelect, 0, 3)


        self.btnStringFunc = QtWidgets.QPushButton(self.buttons_container)
        self.btnStringFunc.setMinimumSize(QtCore.QSize(0, 40))
        self.btnStringFunc.setStyleSheet(button_style)
        self.btnStringFunc.setObjectName("btnStringFunc")
        self.gridLayout_buttons.addWidget(self.btnStringFunc, 1, 0)

        self.btnMasterJoin = QtWidgets.QPushButton(self.buttons_container)
        self.btnMasterJoin.setMinimumSize(QtCore.QSize(0, 40))
        self.btnMasterJoin.setStyleSheet(button_style)
        self.btnMasterJoin.setObjectName("btnMasterJoin")
        self.gridLayout_buttons.addWidget(self.btnMasterJoin, 1, 1)

        self.btnBackMain = QtWidgets.QPushButton(self.buttons_container)
        self.btnBackMain.setMinimumSize(QtCore.QSize(0, 40))
        self.btnBackMain.setStyleSheet(button_style)  # Такая же стилизация как у остальных
        self.btnBackMain.setObjectName("btnBackMain")
        self.gridLayout_buttons.addWidget(self.btnBackMain, 1, 2)

        # Добавляем контейнер кнопок в главный layout
        self.verticalLayout_main.addWidget(self.buttons_container)

        # ОБЛАСТЬ ДЛЯ РЕЗУЛЬТАТОВ/ТАБЛИЦ (стиль как в MainMenu.py)
        self.results_container = QtWidgets.QWidget(Form)
        self.results_container.setObjectName("results_container")
        self.results_container.setStyleSheet("""
            background-color: rgba(16, 30, 41, 240);
            border: 1px solid rgba(46, 82, 110, 255);
            border-radius: 5px;
        """)
        self.verticalLayout_main.addWidget(self.results_container)

        # Устанавливаем соотношения для растяжения
        self.verticalLayout_main.setStretch(0, 0)  # Заголовок - не растягивается
        self.verticalLayout_main.setStretch(1, 0)  # Кнопки - не растягивается
        self.verticalLayout_main.setStretch(2, 1)  # Область результатов - растягивается

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Меню Администратора"))
        self.title_label.setText(_translate("Form", "Панель управления базой данных"))
        self.createSchemaButton.setText(_translate("Form", "Создать схему"))
        self.deleteSchemaButton.setText(_translate("Form", "Удалить схему"))
        self.btnAlterTable.setText(_translate("Form", "Изменить таблицу"))
        self.btnSelect.setText(_translate("Form", "SELECT запросы"))
        self.btnStringFunc.setText(_translate("Form", "Строковые функции"))
        self.btnMasterJoin.setText(_translate("Form", "Мастер соединений"))
        self.btnBackMain.setText(_translate("Form", "Главное меню"))