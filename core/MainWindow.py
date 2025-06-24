from .common import *
from .SideBar import SideBar
from .Signals import Signals
from .ChatWindow import ChatList
from .FontSetting import set_font
from .Agent_1 import MyChatAgent
from .ImageAgent import ImageAgent
from .Model import model, vision_model
from functools import partial
from core.api_saver import ApiKeySaver
from .RAG import RAGStorage
import tkinter as tk
from tkinter import filedialog

log = logging.getLogger(__name__)

class AgentInitializer(QThread):
    agents_ready = Signal(object, object, object)  # chat_agent, image_agent

    def run(self):
        # 在子线程中执行耗时初始化
        chat_agent = MyChatAgent(model=model)
        image_agent = ImageAgent(vision_model)
        rag_storage = RAGStorage(similarity_threshold=0.6, top_k=1)
        self.agents_ready.emit(chat_agent, image_agent, rag_storage)


class MainWindow(QMainWindow):

    def __init__(self, app, width=1000, height=600):

        super().__init__()
        self.setWindowTitle("Bugsy")
        self.setWindowIcon(QIcon("Pet/res/icons/icon.png"))

        # 获取屏幕尺寸，设置主窗口位置
        self.resize(width, height)
        screen_geometry = app.primaryScreen().availableGeometry()
        self.move(
            screen_geometry.width() // 2 - width // 2,
            screen_geometry.height() // 2 - height // 2,
        )

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: palette(window);  
            }
        """
        )

        # 设置空变量等待赋值
        self.chat_agent = None
        self.image_agent = None
        self.rag_storage = None

        # 初始化界面结构
        self.setup_ui_structure()

        # 启动异步 agent 加载线程
        self.agent_loader = AgentInitializer()
        self.agent_loader.agents_ready.connect(self.on_agents_ready)
        self.agent_loader.start()

    def refresh(self):
        self.chat_agent.change_model(model)
        self.image_agent.change_model(vision_model)
        self.loading_label.setVisible(False)
        self.main_content_widget.setVisible(True)

    def on_agents_ready(self, chat_agent, image_agent, rag_storage):
        self.chat_agent = chat_agent
        self.image_agent = image_agent
        self.rag_storage = rag_storage

        # 注册信号连接
        Signals.instance().to_chat_agent_signal.connect(
            lambda x: self.chat_agent.receive_message(x, 1)
        )
        Signals.instance().to_debug_agent_signal.connect(
            lambda x: self.chat_agent.receive_message(x, 0)
        )
        Signals.instance().to_image_agent_signal.connect(
            lambda img, question, is_path: self.image_agent.receive_message(
                img, question, is_path
            )
        )
        Signals.instance().to_rag_agent_signal.connect(
            lambda x: self.chat_agent.receive_message(x, 3)
        )

        # ==== 加载完成：切换 UI ====
        self.loading_label.setVisible(False)
        self.main_content_widget.setVisible(True)

        print("AI agents 初始化完成")

    def setup_ui_structure(self):

        self.animations = {}

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)
        self.central_widget.setLayout(self.outer_layout)

        # ===== 加载提示页面 =====
        self.loading_label = QLabel("正在加载 AI 模型，请稍候...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 18px; padding: 20px;")
        self.outer_layout.addWidget(self.loading_label)

        # ===== 主内容区域（顶栏 + 主体） =====
        self.main_content_widget = QWidget()
        self.main_content_widget.setVisible(False)
        self.outer_layout.addWidget(self.main_content_widget)

        self.main_content_layout = QVBoxLayout()
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content_layout.setSpacing(0)
        self.main_content_widget.setLayout(self.main_content_layout)

        # ========== 顶部栏 ==========
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(10, 10, 0, 0)
        self.top_bar.addStretch()

        self.api_saver_button = QPushButton("设置API密钥")
        self.api_saver_button.setFixedHeight(28)
        self.api_saver_button.setStyleSheet("QPushButton { padding: 4px 12px; }")
        self.api_saver_button.clicked.connect(self.show_api_saver_window)
        self.top_bar.addWidget(self.api_saver_button)

        self.main_content_layout.addLayout(self.top_bar)

        # ========== 主体内容区域 ==========
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_content_layout.addLayout(self.main_layout)

        self.sidebar = SideBar(self)
        self.sidebar.setMaximumWidth(230)
        self.main_layout.addWidget(self.sidebar)

        self.main_stack = QStackedWidget()
        self.main_layout.addWidget(self.main_stack)

        # 连接sidebar的信号
        Signals.instance().page_change_signal.connect(
            partial(self.navigate_to, stack=self.main_stack)
        )

        # 通过名称记录页面，使用字典映射
        self.main_stack_map = {}  # 名称→索引

        # 设置 main_stack各页面的内容，注意初始化顺序
        self.chat_inputs = {}  # 页面名 -> QTextEdit
        self.chat_lists = {}  # 页面名 -> ChatList
        self.setup_chatting_window()  # 主界面
        self.have_api_saver_window = False
        self.sidebar_visible = True

    def show_api_saver_window(self):
        if not self.have_api_saver_window:
            self.api_saver_window = ApiKeySaver(self)
            self.api_saver_window.show()
            self.have_api_saver_window = True
        # 1. 取消最小化（恢复正常大小）
        self.api_saver_window.setWindowState(
            self.api_saver_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
        )

        # 2. 置顶显示
        self.api_saver_window.raise_()  # 提升到其他窗口上方
        self.api_saver_window.activateWindow()  # 激活为当前活动窗口

    def create_debug_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout = QHBoxLayout()
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

        title_label = QLabel("Debug")
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

    def create_chat_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout = QHBoxLayout()
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

        top_layout = QHBoxLayout()
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

        # 发送按钮+图片选择
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(0)

        self.img_path_edit = QLineEdit()
        self.img_path_edit.setFixedHeight(35)
        self.img_path_edit.setStyleSheet(
            """QLineEdit {
					border-radius: 5px;
					border:1px solid palette(mid);
					background:transparent
				}"""
        )
        self.img_path_edit.setPlaceholderText("请选择图片路径")
        set_font(self.img_path_edit)
        bottom_layout.addWidget(self.img_path_edit)

        img_btn = QPushButton("浏览...")
        img_btn.setFixedSize(80, 35)
        img_btn.setStyleSheet(
            """
		                QPushButton {
		                    background-color: transparent;
		                    border: 1px solid palette(mid);
		                    border-radius: 4px;
		                    padding: 0px;
		                    text-align: center;
		                }
		                QPushButton:hover {
		                    background-color: palette(midlight); /*轻微高亮*/
		                    border-radius: 4px;
		                }
		                QPushButton:pressed {
							background-color: palette(mid);
						}
		            """
        )
        set_font(img_btn)
        img_btn.clicked.connect(self.select_img_path)
        bottom_layout.addWidget(img_btn)

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
        bottom_layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(bottom_layout)
        return chat_widget, input_box, chat_list

    def select_img_path(self):
        """选择图片"""
        if sys.platform == "darwin":
            file_filter = "Images (*.jpg *.png)"
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "", file_filter
            )
        else:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="选择图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp")],
            )
        if file_path:
            self.img_path_edit.setText(file_path)

    def create_rag_window(self):
        chat_widget = QWidget()
        layout = QVBoxLayout()
        chat_widget.setLayout(layout)  # 内容区域布局
        layout.setContentsMargins(20, 5, 20, 20)

        top_layout = QHBoxLayout()
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
        """ "
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
            try :
                chat_list.receive_message(text)
            except :
                chat_list.show_API_error()
