from .common import *
from .Signals import Signals
from .FontSetting import set_font

log = logging.getLogger(__name__)


class ChatMessage(QWidget):
	def __init__(self, message, is_me, avatar_path=None, parent=None):
		"""
		:param message: 消息
		:param is_me: 是否是我发出的
		:param avatar_path: 头像路径 TODO
		"""
		super().__init__(parent)

		# 设置消息布局
		layout = QHBoxLayout()
		if is_me:
			layout.setContentsMargins(50, 5, 10, 5)  # 偏右
		else:
			layout.setContentsMargins(10, 5, 50, 5)  # 偏左

		# TODO:头像
		# avatar_label = QLabel()
		# avatar_pixmap = QPixmap(avatar_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		# avatar_label.setPixmap(avatar_pixmap)

		# 消息气泡
		message_label = QLabel(message)
		message_label.setMinimumHeight(50)
		set_font(message_label)
		message_label.setWordWrap(True)
		if is_me:
			message_label.setStyleSheet("""
					QLabel {
					background: rgb(163,240,135);
					border-radius: 5px;
					padding: 10px;
					color: black;
				}
				""")
		else:
			message_label.setStyleSheet("""
								QLabel {
								background: white;
								border-radius: 5px;
								padding: 8px;
								color: black;
							}
							""")

		# 根据发送者调整布局顺序
		if is_me:
			# 头像在右
			layout.addWidget(message_label, 1)
		# layout.addWidget(avatar_label)
		else:
			# 头像在左
			# layout.addWidget(avatar_label)
			layout.addWidget(message_label, 1)

		self.setLayout(layout)


class ChatList(QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setStyleSheet("""
				    QListWidget::item:selected {
				        background: transparent;
				        border:none;
				        color: palette(text)
				    }
				    QListWidget { 
				    	background: transparent; 
				    	border-bottom: 1px solid black;
				        margin: 0;
				        padding:0;
				    }
				    QListWidget::item {
		        			/* 控制行间距（相邻项的间隔） */
		        			margin: 5px;  
		        	}
					""")

	def receive_message(self, content):
		"""
		接收从文本框传来的信号
		:param content: 内容
		"""
		self.add_message(content, True)
		self.send_message(content)

	def add_message(self, message, is_me):
		"""
		向各个聊天框中添加一个对话框
		:param message: 内容
		:param is_me: 是否是我发出
		"""
		# 创建单个框
		message_widget = ChatMessage(message, is_me)

		# 创建列表项
		item = QListWidgetItem()
		item.setSizeHint(message_widget.sizeHint())

		# 添加项到列表
		self.addItem(item)
		self.setItemWidget(item, message_widget)

		# 滚动到底部
		self.scrollToBottom()

	def send_message(self, content):
		"""向AI发送信息"""
		Signals.instance().send_message_to_ai(content)

	def clear_messages(self):
		"""
        清空聊天列表中的所有消息
        """
		self.clear()  # 调用 QListWidget 自带的清空方法
