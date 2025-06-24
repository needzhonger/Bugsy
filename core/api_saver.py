from core.common import *

class ApiKeySaver(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("保存API密钥")
        self.setFixedSize(400, 150)
        self.parent = parent

        # 创建布局
        layout = QVBoxLayout()

        # 创建输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入您的 API KEY")
        layout.addWidget(self.input_field)

        # 创建按钮
        self.save_button = QPushButton("保存API密钥")
        self.save_button.clicked.connect(self.save_api_key)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_api_key(self):
        api_key = self.input_field.text().strip()

        if not api_key:
            QMessageBox.warning(self, "错误", "请输入有效的 API KEY")
            return

        # 获取脚本文件所在目录的上一级（即 core 目录）
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.abspath(os.path.join(current_script_dir, ".."))
        file_path = os.path.join(core_dir, "API_KEY.env")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"API_KEY={api_key}\n")
            QMessageBox.information(self, "成功", f"API密钥已保存至:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def closeEvent(self, event: QCloseEvent):
        self.parent.have_api_saver_window = False
        event.accept()