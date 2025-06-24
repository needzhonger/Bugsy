from .common import *
from .Signals import Signals
import time
import random
from markdown import markdown

log = logging.getLogger(__name__)


class ChatList(QTextEdit):
    def __init__(self, id, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setStyleSheet(
            """
            QTextEdit {
                border: none;
                border-top: 1px solid palette(text); 
                border-bottom: 1px solid palette(text);  
                background-color: palette(base);   
            }
            """
        )

        self.id = id
        self.img = None  # 图片
        self.rag_query = None  # rag搜索结果

        # self.pending_code_block = None  # 未闭合的代码块缓存

        # 聊天状态控制
        self.waiting_for_ai = False  # AI是否正在响应
        self.has_typing_indicator = False  # 判断“思考中……”标签是否存在
        self.current_ai_response = False  # 判断是否是AI第一次响应

        self.setReadOnly(True)
        self.setAcceptRichText(True)

        # 新增：存储所有消息内容和当前AI响应内容
        self.all_messages = []  # 存储所有消息 {sender, content}
        self.current_ai_content = ""  # 当前AI响应累积的内容

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
                    background-color: #8CAFC3;
                    border-radius: 18px 18px 0 18px;
                    padding: 10px 15px;
                    margin-bottom: 5px;
                }}
                .ai-message {{
                    border: 1px solid #D9C7B8;
                    border-radius: 18px 18px 18px 0;
                    padding: 10px 15px;
                    margin-bottom: 5px;
                }}
                pre {{
                    background-color: #96A587;
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
        # self.messages_html = ""

    def _add_message(self, sender, content):
        """添加消息到聊天记录"""
        self.all_messages.append({"sender": sender, "content": content})
        self._update_chat_display()

    def _update_chat_display(self):
        """更新聊天显示区域"""
        messages_html = ""
        for msg in self.all_messages:
            if msg["sender"] == "ai" and msg["content"].startswith("<markdown>"):
                # 处理AI的Markdown消息
                markdown_content = msg["content"][10:]  # 去掉<markdown>标记
                html_content = self._markdown_to_html(markdown_content)
                messages_html += f"""
                <div class="message-container">
                    <div class="ai-message">
                        {html_content}
                    </div>
                </div>
                """
            else:
                # 普通消息（用户消息或系统消息）
                content = msg["content"].replace("\n", "<br>")
                messages_html += f"""
                <div class="message-container">
                    <div class="{msg["sender"]}-message">
                        {content}
                    </div>
                </div>
                """

        # 添加思考中指示器（如果需要）
        if self.has_typing_indicator:
            messages_html += """
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

        full_html = self.html_template.format(messages=messages_html)
        self.setHtml(full_html)
        # 滚动到底部
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _markdown_to_html(self, text: str) -> str:
        """将Markdown转为HTML，并处理代码块"""
        from markdown import markdown

        # 转换Markdown
        html = markdown(text, extensions=["fenced_code", "tables"])

        # 后处理（添加CSS样式）
        styled_html = f"""
        <style>
            pre {{ 
                background: #E8EDDF;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            code {{ font-family: Consolas; }}
        </style>
        {html}
        """
        return styled_html

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
        self.has_typing_indicator = True
        self._update_chat_display()

    def _remove_typing_indicator(self):
        """移除'思考中……'"""
        self.has_typing_indicator = False
        self._update_chat_display()

    def start_ai_response(self, *user_message):
        """发送给AI"""
        # 清空当前AI响应
        self.current_ai_content = ""
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

    def update_ai_response(self, content:str):
        """接收AI回答"""
        # 移除"思考中……"指示器
        if self.has_typing_indicator:
            self._remove_typing_indicator()

        if content == "<EOS>":
            # 响应完成，添加完整的AI消息
            if self.current_ai_content:
                self._add_message("ai", f"<markdown>{self.current_ai_content}")
            self._enable_user_input()

        else:
            # 累积AI响应内容
            self.current_ai_content += content
            # 更新显示（每次都会重新渲染整个AI消息）
            if self.current_ai_content:
                # 临时添加当前内容（带<markdown>标记）
                temp_messages = self.all_messages.copy()
                temp_messages.append(
                    {"sender": "ai", "content": f"<markdown>{self.current_ai_content}"}
                )
                self._render_temp_messages(temp_messages)

    def _render_temp_messages(self, messages):
        """临时渲染消息（用于流式更新）"""
        messages_html = ""
        for msg in messages:
            if msg["sender"] == "ai" and msg["content"].startswith("<markdown>"):
                markdown_content = msg["content"][10:]
                html_content = self._markdown_to_html(markdown_content)
                messages_html += f"""
                <div class="message-container">
                    <div class="ai-message">
                        {html_content}
                    </div>
                </div>
                """
            else:
                content = msg["content"].replace("\n", "<br>")
                messages_html += f"""
                <div class="message-container">
                    <div class="{msg["sender"]}-message">
                        {content}
                    </div>
                </div>
                """

        if self.has_typing_indicator:
            messages_html += """
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

        full_html = self.html_template.format(messages=messages_html)
        self.setHtml(full_html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _enable_user_input(self):
        """完成AI响应后启用用户输入"""
        self.waiting_for_ai = False
        print(f"ChatWindow{self.id} AI响应完成")

    def get_ai_response(self, data_list: list, min_delay=0.01, max_delay=0.15):
        print(f"ChatWindow(id={self.id})收到ai回复")
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

    def show_API_error(self):
        #TODO 在API错误时在聊天框中显示“API错误”的提醒
        pass
