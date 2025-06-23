from .common import *
from .Signals import Signals
import time
import random

log = logging.getLogger(__name__)


class ChatList(QTextEdit):
    def __init__(self, id, parent=None):
        super().__init__(parent)

        self.setStyleSheet(
            """
            QTextEdit {
                border: none;
                border-top: 1px solid palette(text); 
                border-bottom: 1px solid palette(text);  
                background-color: #FAFAF7;   
            }
            """
        )

        self.id = id
        self.img = None  # 图片
        self.rag_query = None  # rag搜索结果

        # 聊天状态控制
        self.waiting_for_ai = False  # AI是否正在响应
        self.has_typing_indicator = False  # 判断“思考中……”标签是否存在
        self.current_ai_response = False  # 判断是否是AI第一次响应

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
                }}
                .message-container {{
                    margin-bottom: 15px;
                    clear: both;
                }}
                .user-message {{
                    background-color: #E8F0F5;
                    border-radius: 18px 18px 0 18px;
                    padding: 10px 15px;
                    margin-bottom: 5px;
                }}
                .ai-message {{
                    background-color: #E8EDDF;
                    border: 1px solid #D9C7B8;
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
            content = content.replace("\n", "<br>")
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

        # 更新
        QApplication.instance().processEvents()

        # 发送给AI
        self.start_ai_response(user_text)

    def _show_typing_indicator(self):
        """显示'思考中……'"""
        self.messages_html += """
        <div class="message-container">
            <div class="ai-message">
                思考中……<span class="typing-indicator">
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
        """移除'思考中……'"""
        self.messages_html = self.messages_html[: self.messages_html.rfind("思考中……")]
        self._update_chat_display()
        self.has_typing_indicator = False

    def start_ai_response(self, *user_message):
        """发送给AI"""
        # 清空当前AI响应
        self.current_ai_response = False
        # 发送
        if self.id == 0:  # debug窗口
            Signals.instance().send_message_to_debug_agent(user_message[0])
        elif self.id == 1:  # 文字处理窗口
            Signals.instance().send_message_to_ai(user_message[0])
        elif self.id == 2:  # 图片处理窗口:图片、问题、是否是路径
            Signals.instance().send_message_to_image_agent(
                user_message[0], user_message[1], user_message[2]
            )
        else:  # rag窗口
            Signals.instance().send_message_to_rag_agent(user_message[0])

    def update_ai_response(self, content):
        """接收AI回答"""
        # 移除"思考中……"指示器
        if self.has_typing_indicator:
            self._remove_typing_indicator()

        if content == "<EOS>":
            # 响应完成,允许用户输入
            self._enable_user_input()

        else:
            if self.waiting_for_ai:
                # 如果是第一个块，先添加AI消息容器
                if not self.current_ai_response:
                    self.messages_html += """
                    <div class="message-container">
                        <div class="ai-message">
                    """
                    self.current_ai_response = True

                # 如果是代码块（简单检测）TODO

                # 如果不是
                content = content.replace("\n", "<br>")
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
        print(f"ChatWindow{id}AI响应完成")
        self.waiting_for_ai = False

    def get_ai_response(self, data_list: list, min_delay=0.01, max_delay=0.15):
        print(f"ChatWindow(id={id})收到ai回复")
        # print(data_list)
        # 图片识别不支持流式响应，一次性回复
        data_list.append("<EOS>")  # 保证gui的输出一定能正常结束
        for item in data_list:
            if self.waiting_for_ai:
                self.update_ai_response(item)
                # 更新
                QApplication.instance().processEvents()
                # 在词语间添加随机延迟
                time.sleep(random.uniform(min_delay, max_delay))
            else:
                break
