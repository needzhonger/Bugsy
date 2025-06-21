from .common import *
from .Signals import Signals

log = logging.getLogger(__name__)


class ChatList(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            """
            QTextEdit {
                border: none;
                border-bottom: 1px solid palette(text);  
            }
            """
        )

        # 聊天状态控制
        self.waiting_for_ai = False
        self.has_typing_indicator = False
        self.timeout = False
        self.current_ai_response = ""
        self.response_timer = None

        self.setReadOnly(True)
        self.setAcceptRichText(True)

        self._setup_html_template()

    def _setup_html_template(self):
        """设置HTML/CSS模板"""
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 16px;
                    margin: 0;
                    padding: 10px;
                    background-color: #f5f5f5;
                }}
                .message-container {{
                    margin-bottom: 15px;
                    clear: both;
                }}
                .user-message {{
                    background-color: #DEDEDE;
                    border-radius: 18px 18px 0 18px;
                    padding: 10px 15px;
                    margin-bottom: 5px;
                }}
                .ai-message {{
                    border: 1px solid #ddd;
                    border-radius: 18px 18px 18px 0;
                    padding: 10px 15px;
                    margin-bottom: 5px;
                }}
                pre {{
                    background-color: #f0f0f0;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                    font-family: 'Consolas', monospace;
                }}
                .typing-indicator {{
                    display: inline-block;
                    margin-left: 5px;
                }}
                .typing-dot {{
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background-color: #888;
                    margin-right: 3px;
                    opacity: 0;
                    animation: typingAnimation 1.4s infinite ease-in-out;
                }}
                .typing-dot:nth-child(1) {{ animation-delay: 0s; }}
                .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
                .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
                @keyframes typingAnimation {{
                    0% {{ opacity: 0.3; transform: translateY(0); }}
                    50% {{ opacity: 1; transform: translateY(-3px); }}
                    100% {{ opacity: 0.3; transform: translateY(0); }}
                }}
            </style>
        </head>
        <body>
            {messages}
        </body>
        </html>
        """
        self.messages_html = ""

    def _add_message(self, sender, content, is_code=False):
        """添加消息到聊天记录"""
        if is_code:
            message_html = f"""
            <div class="message-container">
                <div class="{sender}-message">
                    <pre><code>{content}</code></pre>
                </div>
            </div>
            """
        else:
            message_html = f"""
            <div class="message-container">
                <div class="{sender}-message">
                    {content}
                </div>
            </div>
            """

        self.messages_html += message_html
        self._update_chat_display()

    def _update_chat_display(self):
        """更新聊天显示区域"""
        full_html = self.html_template.format(messages=self.messages_html)
        self.setHtml(full_html)
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def receive_message(self, user_text):
        """处理用户发送消息"""
        if self.waiting_for_ai:
            return

        # 添加用户消息
        self._add_message("user", user_text)

        # 禁用输入
        self.waiting_for_ai = True

        # 显示AI正在输入指示器
        self._show_typing_indicator()

        # 发送给AI
        self.start_ai_response(user_text)

    def _show_typing_indicator(self):
        """显示AI正在输入的动画"""
        self.messages_html += """
        <div class="message-container">
            <div class="ai-message">
                思考中<span class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </span>
            </div>
        </div>
        """
        self._update_chat_display()
        self.has_typing_indicator = True

    def _remove_typing_indicator(self):
        """移除AI正在输入的动画"""
        self.messages_html = self.messages_html[: self.messages_html.rfind("思考中")]
        self._update_chat_display()
        self.has_typing_indicator = False

    def start_ai_response(self, user_message):
        """发送给AI"""
        # 清空当前AI响应
        self.current_ai_response = ""

        # 发送
        Signals.instance().send_message_to_ai(user_message)

    def now_is_timeout(self):
        self.timeout = True
        self._enable_user_input()

    def update_ai_response(self, content):
        """接收AI回答"""
        # 移除"正在输入"指示器
        if self.has_typing_indicator:
            self._remove_typing_indicator()

        if content == "<EOS>" or self.timeout:
            # 响应完成或超时,允许用户输入
            self._enable_user_input()

        else:
            if self.waiting_for_ai:

                # 20s后，视为超时，响应强制停止
                self.timeout = False
                # 如果已有计时器，先停止
                if self.response_timer and self.response_timer.isActive():
                    self.response_timer.stop()
                # 创建定时器
                self.response_timer = QTimer()
                self.response_timer.setSingleShot(True)  # 设置为单次触发
                # 连接超时信号到回调函数
                self.response_timer.timeout.connect(self.now_is_timeout)
                # 启动定时器
                self.response_timer.start(20000)

                # 如果是第一个块，先添加AI消息容器
                if not self.current_ai_response:
                    self.messages_html += """
                    <div class="message-container">
                        <div class="ai-message">
                    """

                self.current_ai_response += content + "<br>"

                # 如果是代码块（简单检测）TODO
                self.messages_html += content

                # 更新显示
                self._update_chat_display()

    def _enable_user_input(self):
        """完成AI响应后启用用户输入"""
        # 关闭AI消息容器
        self.messages_html += """
                </div>
            </div>
        """
        self._update_chat_display()
        self.waiting_for_ai = False
        if self.response_timer and self.response_timer.isActive():
            self.response_timer.stop()
