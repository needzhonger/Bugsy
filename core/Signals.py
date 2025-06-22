from PySide6.QtCore import Signal, QObject
from .common import *

log = logging.getLogger(__name__)


class Signals(QObject):
    """
    发送信号的类，只有一个实例
    """

    _instance = None
    page_change_signal = Signal(str)  # 翻页信号
    to_chat_agent_signal = Signal(str)  # 向AI发送问题的信号
    chat_agent_response_signal = Signal(str)  # AI回复的信号
    to_debug_agent_signal = Signal(str)
    debug_agent_response_signal = Signal(str)
    to_image_agent_signal = Signal(Image.Image, str, bool)
    image_agent_response_signal = Signal(str)
    to_rag_agent_signal = Signal(str)
    rag_agent_response_signal = Signal(str)

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
        向chat_agent发送问题
        """
        # print("in send_message_to_ai")
        self.to_chat_agent_signal.emit(content)

    def send_ai_response(self, response):
        """
        发送chat_agent回复
        """
        self.chat_agent_response_signal.emit(response)

    def send_message_to_dabug_agent(self, content: str):
        self.to_debug_agent_signal.emit(content)

    def send_debug_agent_response(self, content: str):
        self.debug_agent_response_signal.emit(content)

    def send_message_to_image_agent(self, img, question: str, is_path=False):
        self.to_image_agent_signal.emit(img, question, is_path)

    def send_image_agent_response(self, content: str):
        self.image_agent_response_signal.emit(content)

    def send_message_to_rag_agent(self, content: str):
        self.to_rag_agent_signal.emit(content)

    def send_rag_agent_response(self, content: str):
        self.rag_agent_response_signal(content)
