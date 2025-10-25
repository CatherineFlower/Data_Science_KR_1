import sys
from Application import Application
from LoginWindow import LoginWindow


def main():
    app = Application(sys.argv)

    login_window = LoginWindow()
    login_window.show()

    result = app.exec_()
    sys.exit(result)


if __name__ == "__main__":
    main()