from PySide6.QtCore import Signal, QObject
from .common import *

log = logging.getLogger(__name__)

class Signals(QObject):
	"""
	发送信号的类，只有一个实例
	"""
	_instance = None
	page_change_signal = Signal(str)  # 翻页信号
	message_to_chat_agent_signal = Signal(str)  # 向AI发送问题的信号
	chat_agent_response_signal = Signal(str)  # AI回复的信号

	@staticmethod
	def instance() -> "Signals":
		if Signals._instance is None:
			Signals._instance = Signals()
		return Signals._instance

	def __init__(self):
		super().__init__()

	def send_page_change_signal(self, name):
		"""
		向 main_stack发送改变页面的信号
		"""
		self.page_change_signal.emit(name)

	def send_message_to_ai(self, content):
		"""
		向AI发送问题
		"""
		# print("in send_message_to_ai")
		self.message_to_chat_agent_signal.emit(content)

	def send_ai_response(self,response):
		"""
		发送AI回复
		"""
		self.chat_agent_response_signal.emit(response)
