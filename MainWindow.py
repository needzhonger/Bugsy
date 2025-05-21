from common import *
from SideBar import SideBar
from functools import partial
from Signals import Signals
from ChatWindow import ChatList
from FontSetting import set_font
from OneAgent import MyChatAgent, model

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):

	def __init__(self, app, width=1000, height=600):
		super().__init__()
		self.setWindowTitle("Programmer")

		# 获取屏幕尺寸，设置主窗口位置
		self.resize(width, height)
		screen_geometry = app.primaryScreen().availableGeometry()
		self.move(screen_geometry.width() // 2 - width // 2, screen_geometry.height() // 2 - height // 2)

		# 动画管理集
		self.animations: dict[str, QPropertyAnimation] = {}

		# 主窗口中心部件（容纳 main_layout）
		self.central_widget = QWidget()
		self.setCentralWidget(self.central_widget)

		# 主布局 main_layout（容纳侧边栏和主窗口）
		self.main_layout = QHBoxLayout()
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(0)
		self.central_widget.setLayout(self.main_layout)

		# 侧边栏
		self.sidebar = SideBar(self)
		self.sidebar.setMaximumWidth(230)  # 设置初始宽度为230
		self.main_layout.addWidget(self.sidebar)
		self.sidebar_visible = True  # 初始化侧边栏状态
		self.setup_sidebar_animation()

		# 主窗口（设计为堆叠窗口，有多个界面）
		self.main_stack = QStackedWidget()
		self.main_layout.addWidget(self.main_stack)

		# 连接sidebar的信号
		Signals.instance().page_change_signal.connect(partial(self.navigate_to, stack=self.main_stack))

		# 通过名称记录页面，使用字典映射
		self.main_stack_map = {}  # 名称→索引

		# 设置 main_stack各页面的内容，注意初始化顺序
		self.setup_chatting_window()  # 主界面

		# 设置AI
		self.chat_agent = MyChatAgent(model=model)
		Signals.instance().message_to_chat_agent_signal.connect(lambda x: self.chat_agent.stream_response(x))

	def setup_chatting_window(self):
		"""
		main_window创建
		"""
		self.chatting_window = QWidget()

		layout = QVBoxLayout()  # 内容区域布局
		layout.setContentsMargins(20, 5, 20, 20)
		self.chatting_window.setLayout(layout)

		sidebar_btn = QPushButton('<')  # 控制侧边栏的按钮
		sidebar_btn.setStyleSheet("""
								QPushButton {
								background-color: transparent;
								border: none;
								padding: 0;
								margin: 0;
								text-align: center;
								color: #a0a0a0;
								}
								QPushButton:hover {
								color: #07C160;
								}
								QPushButton:pressed {
								color: #05974C;
								}
								""")
		set_font(sidebar_btn)
		sidebar_btn.clicked.connect(partial(self.toggle_sidebar, btn=sidebar_btn))
		layout.addWidget(sidebar_btn, alignment=Qt.AlignmentFlag.AlignLeft)

		self.chat_list = ChatList()  # 对话框
		# 连接信号，用于发消息
		Signals.instance().chat_agent_response_signal.connect(lambda message: self.chat_list.add_message(message, False))
		layout.addWidget(self.chat_list)

		# 输入文本框
		self.input_box = QTextEdit()
		self.input_box.setMaximumHeight(100)
		set_font(self.input_box)
		self.input_box.setStyleSheet("""
						            QTextEdit {
						                background: transparent;
						                border: none;
						                border-radius: 5px;
						                padding: 5px;
						            }
						        """)
		layout.addWidget(self.input_box)

		# 发送按钮
		send_btn = QPushButton("发送")
		send_btn.setFixedSize(100, 30)
		set_font(send_btn)
		send_btn.setStyleSheet("""
				QPushButton {
                    background-color: palette(midlight);
                    border: none;
                    color: #07C160;
                    padding: 0px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: palette(mid);
                    border-radius: 4px;
                }
                QPushButton:pressed {
					background-color: palette(mid);
				}
				""")
		send_btn.clicked.connect(self.send_message)
		layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)

		# 添加到stack
		self.add_page(self.main_stack, self.chatting_window, "ChattingWindow")

	def add_page(self, stack: QStackedWidget, widget: QWidget, name: str):
		""""
		向 stack 中添加页面
		"""
		self.main_stack_map[name] = stack.addWidget(widget)

	def navigate_to(self, name: str, stack: QStackedWidget):
		"""
		通过名称跳转页面
		"""
		if name in self.main_stack_map:
			stack.setCurrentIndex(self.main_stack_map[name])
		else:
			print(f"MainWindow @ navigate_to:错误：未知页面 {name}!")

	def setup_sidebar_animation(self) -> None:
		"""侧边栏展开动画设置"""
		self.animations["sidebar"] = QPropertyAnimation(self.sidebar, b"maximumWidth")
		self.animations["sidebar"].setDuration(300)
		self.animations["sidebar"].setEasingCurve(QEasingCurve.Type.InOutQuad)

	def toggle_sidebar(self, btn) -> None:
		"""处理sidebar的变化"""
		self.sidebar_visible = not self.sidebar_visible

		if self.sidebar_visible:
			self.animations["sidebar"].setStartValue(0)
			self.animations["sidebar"].setEndValue(230)
			btn.setText("<")
		else:
			self.animations["sidebar"].setStartValue(230)
			self.animations["sidebar"].setEndValue(0)
			btn.setText(">")

		self.animations["sidebar"].start()

	def send_message(self):
		"""向ChatList发送信号"""
		message = self.input_box.toPlainText().strip()
		self.input_box.clear()
		if message:
			self.chat_list.receive_message(message)
