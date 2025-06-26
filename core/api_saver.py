from core.common import *
from core.Model import init_models

class ModelLoaderThread(QThread):
    done = Signal(object, object)  # 任务完成时发出信号

    def run(self):
        new_model, new_image_model = init_models()  # 子线程中执行耗时操作
        self.done.emit(new_model, new_image_model)  # 通知主线程

def encode(api_key):
    res = ""
    for i in api_key :
        res += chr(ord(i) + 3)
    return res
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
        api_key = encode(api_key)
        if not api_key:
            QMessageBox.warning(self, "错误", "请输入有效的 API KEY")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, "API_KEY.env")

        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"API_KEY={api_key}\n")
            self.parent.loading_label.setVisible(True)
            self.parent.main_content_widget.setVisible(False)
            # 启动子线程加载模型
            self.loader_thread = ModelLoaderThread()
            self.loader_thread.done.connect(self.after_model_loaded)
            self.loader_thread.start()

            QMessageBox.information(self, "成功", f"API密钥已保存至:\n{env_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def after_model_loaded(self, new_model, new_image_model):
        self.close()  # 安全地关闭窗口
        self.parent.refresh(new_model, new_image_model)  # 通知父组件刷新

    def closeEvent(self, event: QCloseEvent):
        self.parent.have_api_saver_window = False
        event.accept()