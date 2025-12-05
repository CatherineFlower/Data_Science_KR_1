import sys
import os

# Установка пути к плагинам Qt для Windows
if sys.platform == 'win32':
    try:
        import PyQt5
        qt5_path = os.path.dirname(PyQt5.__file__)
        plugins_path = os.path.join(qt5_path, 'Qt5', 'plugins')
        if os.path.exists(plugins_path):
            os.environ['QT_PLUGIN_PATH'] = plugins_path
    except ImportError:
        pass

from Application import Application
from LoginWindow import LoginWindow


def main():
    app = Application(sys.argv)

    # Создаем и показываем окно входа вместо главного окна
    login_window = LoginWindow()
    login_window.show()

    result = app.exec_()
    sys.exit(result)


if __name__ == "__main__":
    main()