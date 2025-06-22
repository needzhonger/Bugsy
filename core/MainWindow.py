from .common import *
from .SideBar import SideBar
from .Signals import Signals
from .ChatWindow import ChatList
from .FontSetting import set_font
from .Agent_1 import MyChatAgent
from .Model import model
from functools import partial
from .register_and_login.ui_login import LoginWindow
from .register_and_login.ui_register import RegisterWindow

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self, app, width=1000, height=600):

        super().__init__()
        self.setWindowTitle("Bugsy")
        self.setWindowIcon(QIcon("Pet/res/icons/icon.png"))

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

        # 原来的 main_layout 改为放入 outer_layout
        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        self.central_widget.setLayout(self.outer_layout)

        # 顶部栏布局
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(10, 10, 10, 0)

        # 添加弹性空间，使按钮靠右
        self.top_bar.addStretch()

        # 登录按钮
        self.have_login_window = False # 标记是否已经存在登录窗口，避免重复加载登录窗口
        self.login_window = None
        self.login_button = QPushButton("登录")
        self.login_button.setFixedHeight(28)
        self.login_button.setStyleSheet("QPushButton { padding: 4px 12px; }")
        self.login_button.clicked.connect(self.show_login_window)

        # 注册按钮
        self.have_register_window = False  # 标记是否已经存在注册窗口，避免重复加载注册窗口
        self.login_window = None
        self.register_button = QPushButton("注册")
        self.register_button.setFixedHeight(28)
        self.register_button.setStyleSheet("QPushButton { padding: 4px 12px; }")
        self.register_button.clicked.connect(self.show_register_window)

        self.top_bar.addWidget(self.login_button)
        self.top_bar.addWidget(self.register_button)

        # 添加顶部栏和主区域布局
        self.outer_layout.addLayout(self.top_bar)
        self.outer_layout.addLayout(self.main_layout)

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
        self.chat_inputs = {}  # 页面名 -> QTextEdit
        self.chat_lists = {}  # 页面名 -> ChatList
        self.setup_chatting_window()  # 主界面

        # 设置AI TODO
        self.chat_agent = MyChatAgent(model=model)
        Signals.instance().to_chat_agent_signal.connect(
            lambda x: self.chat_agent.receive_message(x)
        )
        self.debug_agent=None
        self.image_agent=None
        self.rag_agent=None

    def show_login_window(self):
        if not self.have_login_window:
            self.login_window = LoginWindow(self)
            self.login_window.show()
            self.have_login_window = True
        # 1. 取消最小化（恢复正常大小）
        self.login_window.setWindowState(self.login_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        # 2. 置顶显示
        self.login_window.raise_()  # 提升到其他窗口上方
        self.login_window.activateWindow()  # 激活为当前活动窗口

        # QMessageBox.information(self, "登录", "登录窗口弹出（未实现）")

    def show_register_window(self):
        if not self.have_register_window:
            self.register_window = RegisterWindow(self)
            self.register_window.show()
            self.have_register_window = True
        # 1. 取消最小化（恢复正常大小）
        self.register_window.setWindowState(self.register_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

        # 2. 置顶显示
        self.register_window.raise_()  # 提升到其他窗口上方
        self.register_window.activateWindow()  # 激活为当前活动窗口

        # QMessageBox.information(self, "注册", "注册窗口弹出（未实现）")

    def create_debug_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)# 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout=QHBoxLayout()
        layout.addLayout(top_layout)
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
        top_layout.addWidget(sidebar_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch(1)

        title_label=QLabel("DeBug")
        set_font(title_label)
        top_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch(1)

        chat_list = ChatList(0)

        # 连接AI信号 TODO
        Signals.instance().debug_agent_response_signal.connect(
            lambda message: chat_list.get_ai_response(message)
        )
        layout.addWidget(chat_list)

        # 输入文本框
        input_box = QTextEdit()
        input_box.setMaximumHeight(100)
        set_font(input_box)
        input_box.setStyleSheet("""
								            QTextEdit {
								                background: transparent;
								                border: none;
								                border-radius: 5px;
								                padding: 5px;
								            }
								        """)
        layout.addWidget(input_box)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(100, 30)
        set_font(send_btn)
        send_btn.setStyleSheet("""
						QPushButton {
		                    background-color: palette(light);
		                    border: none;
		                    color: #07C160;
		                    padding: 0px;
		                    text-align: center;
		                }
		                QPushButton:hover {
		                    background-color: palette(midlight);
		                    border-radius: 4px;
		                }
		                QPushButton:pressed {
							background-color: palette(mid);
						}
						""")
        send_btn.clicked.connect(partial(self.send_message, input_box, chat_list))
        layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return chat_widget, input_box, chat_list

    def create_chat_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout=QHBoxLayout()
        layout.addLayout(top_layout)
        sidebar_btn = QPushButton("<")  # 控制侧边栏的按钮
        sidebar_btn.setStyleSheet(
                                        """
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
										"""
        )
        set_font(sidebar_btn)
        sidebar_btn.clicked.connect(partial(self.toggle_sidebar, btn=sidebar_btn))
        top_layout.addWidget(sidebar_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch(1)

        title_label = QLabel("文字处理")
        set_font(title_label)
        top_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch(1)

        chat_list = ChatList(1)

        # 连接AI信号 TODO
        Signals.instance().chat_agent_response_signal.connect(
            lambda message: chat_list.get_ai_response(message)
        )
        layout.addWidget(chat_list)

        # 输入文本框
        input_box = QTextEdit()
        input_box.setMaximumHeight(100)
        set_font(input_box)
        input_box.setStyleSheet(
            """
								            QTextEdit {
								                background: transparent;
								                border: none;
								                border-radius: 5px;
								                padding: 5px;
								            }
								        """
        )
        layout.addWidget(input_box)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(100, 30)
        set_font(send_btn)
        send_btn.setStyleSheet(
            """
						QPushButton {
		                    background-color: palette(light);
		                    border: none;
		                    color: #07C160;
		                    padding: 0px;
		                    text-align: center;
		                }
		                QPushButton:hover {
		                    background-color: palette(midlight);
		                    border-radius: 4px;
		                }
		                QPushButton:pressed {
							background-color: palette(mid);
						}
						"""
        )
        send_btn.clicked.connect(partial(self.send_message, input_box, chat_list))
        layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return chat_widget, input_box, chat_list

    def create_image_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout=QHBoxLayout()
        layout.addLayout(top_layout)
        sidebar_btn = QPushButton("<")  # 控制侧边栏的按钮
        sidebar_btn.setStyleSheet(
            """
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
										"""
        )
        set_font(sidebar_btn)
        sidebar_btn.clicked.connect(partial(self.toggle_sidebar, btn=sidebar_btn))
        top_layout.addWidget(sidebar_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch(1)

        title_label = QLabel("图片处理")
        set_font(title_label)
        top_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch(1)

        chat_list = ChatList(2)

        # 连接AI信号 TODO
        Signals.instance().image_agent_response_signal.connect(
            lambda message: chat_list.get_ai_response(message)
        )
        layout.addWidget(chat_list)

        # 输入文本框
        input_box = QTextEdit()
        input_box.setMaximumHeight(100)
        set_font(input_box)
        input_box.setStyleSheet(
            """
								            QTextEdit {
								                background: transparent;
								                border: none;
								                border-radius: 5px;
								                padding: 5px;
								            }
								        """
        )
        layout.addWidget(input_box)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(100, 30)
        set_font(send_btn)
        send_btn.setStyleSheet(
            """
						QPushButton {
		                    background-color: palette(light);
		                    border: none;
		                    color: #07C160;
		                    padding: 0px;
		                    text-align: center;
		                }
		                QPushButton:hover {
		                    background-color: palette(midlight);
		                    border-radius: 4px;
		                }
		                QPushButton:pressed {
							background-color: palette(mid);
						}
						"""
        )
        send_btn.clicked.connect(partial(self.send_message, input_box, chat_list))
        layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return chat_widget, input_box, chat_list

    def create_rag_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout=QHBoxLayout()
        layout.addLayout(top_layout)
        sidebar_btn = QPushButton("<")  # 控制侧边栏的按钮
        sidebar_btn.setStyleSheet(
            """
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
										"""
        )
        set_font(sidebar_btn)
        sidebar_btn.clicked.connect(partial(self.toggle_sidebar, btn=sidebar_btn))
        top_layout.addWidget(sidebar_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch(1)

        title_label = QLabel("文档处理")
        set_font(title_label)
        top_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch(1)

        chat_list = ChatList(3)

        # 连接AI信号 TODO
        Signals.instance().rag_agent_response_signal.connect(
            lambda message: chat_list.get_ai_response(message)
        )
        layout.addWidget(chat_list)

        # 输入文本框
        input_box = QTextEdit()
        input_box.setMaximumHeight(100)
        set_font(input_box)
        input_box.setStyleSheet(
            """
								            QTextEdit {
								                background: transparent;
								                border: none;
								                border-radius: 5px;
								                padding: 5px;
								            }
								        """
        )
        layout.addWidget(input_box)

        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(100, 30)
        set_font(send_btn)
        send_btn.setStyleSheet(
            """
						QPushButton {
		                    background-color: palette(light);
		                    border: none;
		                    color: #07C160;
		                    padding: 0px;
		                    text-align: center;
		                }
		                QPushButton:hover {
		                    background-color: palette(midlight);
		                    border-radius: 4px;
		                }
		                QPushButton:pressed {
							background-color: palette(mid);
						}
						"""
        )
        send_btn.clicked.connect(partial(self.send_message, input_box, chat_list))
        layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return chat_widget, input_box, chat_list

    def setup_chatting_window(self):
        """
		main_window创建
		"""
        # 页面1
        self.chatting_window_1, input_box1, chat_list1 = self.create_debug_window()
        self.chat_inputs["ChattingWindow1"] = input_box1
        self.chat_lists["ChattingWindow1"] = chat_list1
        self.add_page(self.main_stack, self.chatting_window_1, "ChattingWindow1")

        # 页面2
        self.chatting_window_2, input_box2, chat_list2 = self.create_chat_window()
        self.chat_inputs["ChattingWindow2"] = input_box2
        self.chat_lists["ChattingWindow2"] = chat_list2
        self.add_page(self.main_stack, self.chatting_window_2, "ChattingWindow2")

        # 页面3
        self.chatting_window_3, input_box3, chat_list3 = self.create_image_window()
        self.chat_inputs["ChattingWindow1"] = input_box3
        self.chat_lists["ChattingWindow1"] = chat_list3
        self.add_page(self.main_stack, self.chatting_window_3, "ChattingWindow3")

        # 页面4
        self.chatting_window_4, input_box4, chat_list4 = self.create_rag_window()
        self.chat_inputs["ChattingWindow2"] = input_box4
        self.chat_lists["ChattingWindow2"] = chat_list4
        self.add_page(self.main_stack, self.chatting_window_4, "ChattingWindow4")

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
            current_index = stack.currentIndex()
            target_index = self.main_stack_map[name]

            if current_index == target_index:
                # 重复点击，不切换，不清空
                return

            # 切换页面
            stack.setCurrentIndex(target_index)

            # 清空聊天内容
            if name in self.chat_lists:
                self.chat_lists[name].clear()  # 调用 QListWidget 的 clear 方法
            if name in self.chat_inputs:
                self.chat_inputs[name].clear()
        else:
            print(f"MainWindow @ navigate_to: 错误：未知页面 {name}!")

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

    def send_message(self, input_box, chat_list):
        # print("in send_message!")
        text = input_box.toPlainText().strip()
        if text:
            input_box.clear()
            chat_list.receive_message(text)
