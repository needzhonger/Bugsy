from core.common import *
import core.register_and_login.auth as auth

class RegisterWindow(QDialog):
    def __init__(self, parent : QMainWindow = None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("注册")
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.register_btn = QPushButton("注册")

        layout.addWidget(QLabel("用户名"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("密码"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.register_btn)

        self.setLayout(layout)

        self.register_btn.clicked.connect(self.handle_register)

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if auth.register_user(username, password):
            QMessageBox.information(self, "注册成功", "注册成功！请登录")
            self.parent.have_register_window = False
            self.accept()
        else:
            QMessageBox.warning(self, "注册失败", "用户名已存在")

    def closeEvent(self, event: QCloseEvent):
        self.parent.have_register_window = False
        event.accept()