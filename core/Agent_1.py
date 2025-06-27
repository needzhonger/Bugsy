from .common import *
from .Signals import Signals

# chat_agent


class StreamWorker(QThread):
    message_received = Signal(str)
    finished = Signal(int)

    def __init__(self, model, prompt, id, history_messages=None):
        super().__init__()
        self._model = model
        self.prompt = prompt
        self.id = id
        self.history_messages = history_messages or []  # 接收历史消息

    def run(self):
        print("in Agent1")
        api_url = f"{self._model._url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._model._api_key}",
            "Content-Type": "application/json",
        }

        # 构建消息列表：历史消息 + 当前提问
        messages = self.history_messages.copy()
        messages.append({"role": "user", "content": self.prompt})

        data = {
            "model": self._model.model_type,
            "messages": messages,
            "stream": True,
            "max_tokens": 2000,
            "temperature": 0.2,
            "top_p": 0.7,
        }

        try:
            with requests.post(
                api_url, headers=headers, json=data, stream=True, timeout=60
            ) as response:

                if response.status_code != 200:
                    error_msg = f"Agent_1 API请求失败，状态码: {response.status_code}, 错误: {response.text}"
                    print(error_msg)
                    self.message_received.emit(f"[ERROR] {error_msg}")
                    return

                for chunk in response.iter_lines():
                    if chunk:
                        chunk_str = chunk.decode("utf-8").strip()
                        if chunk_str == "[DONE]":
                            break
                        if chunk_str.startswith("data:"):
                            try:
                                chunk_data = json.loads(chunk_str[5:])
                                if chunk_data == " [DONE]":
                                    break
                                content = (
                                    chunk_data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    self.message_received.emit(content)
                            except json.JSONDecodeError as e:
                                print(
                                    f"Agent_1 JSON解析错误: {e}, 原始数据: {chunk_str}"
                                )
        except requests.exceptions.RequestException as e:
            self.message_received.emit(f"[ERROR] 请求异常: {str(e)}")

        self.finished.emit(self.id)


class MyChatAgent(ChatAgent):
    """自定义聊天代理，实现流式响应"""

    def __init__(self, model, output_language="中文"):
        super().__init__(model=model, output_language=output_language)
        self._model = model
        self.result = []  # 记录流式响应结果
        self.history = {}  # 记忆
        self.prompt = ""  # 记录用户的问题

    def _get_history(self, id: int) -> list:
        """获取指定对话ID的历史记录，若无则初始化空列表"""
        if id not in self.history:
            self.history[id] = []
        return self.history[id]

    def stream_response(self, prompt, id: int, history_messages=None):
        self.prompt = prompt
        self.worker = StreamWorker(self._model, prompt, id, history_messages)
        self.worker.message_received.connect(self.send_message)
        self.worker.finished.connect(lambda: self.send_result(id))
        self.worker.start()

    def receive_message(self, message, id: int):
        """接收消息并触发流式响应"""
        print(f"Agent_1开始处理:{message};来自页面{id}")
        history = self._get_history(id)
        self.stream_response(message, id, history)

    def send_message(self, message):
        """记录输出并打印"""
        self.result.append(message)
        print(message)

    def send_result(self, id: int):
        print(f"Agent_1 向ChatWindow(id={id})发送结果")
        if id == 0:
            Signals.instance().send_debug_agent_response(self.result)
        elif id == 1:
            Signals.instance().send_ai_response(self.result)
        elif id == 3:
            Signals.instance().send_rag_agent_response(self.result)

        # 更新历史记录（添加用户提问和AI回复）
        if self.result:
            user_message = {
                "role": "user",
                "content": self.prompt,
            }  # 需确保self.prompt可用
            ai_message = {"role": "assistant", "content": "".join(self.result)}

            history = self._get_history(id)
            history.extend([user_message, ai_message])

            # 限制历史记录长度（避免超出模型token限制）
            max_history = 6  # 保留最近3轮对话
            if len(history) > max_history:
                history = history[-max_history:]
            self.history[id] = history

        self.result.clear()
