from core.common import *
import core.register_and_login.auth as auth
from PySide6.QtGui import QCloseEvent

class LoginWindow(QDialog):
    def __init__(self, parent : QMainWindow = None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("登录")
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("登录")
        self.register_btn = QPushButton("注册")

        layout.addWidget(QLabel("用户名"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("密码"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.register_btn)

        self.setLayout(layout)

        self.login_btn.clicked.connect(self.handle_login)
        self.register_btn.clicked.connect(self.show_register)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if auth.login_user(username, password):
            QMessageBox.information(self, "登录成功", "欢迎回来！")
            self.parent.have_login_window = False
            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误。")

    def closeEvent(self, event: QCloseEvent):
        self.parent.have_login_window = False
        event.accept()

    def show_register(self):
        self.parent.show_register_window()