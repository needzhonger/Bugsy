from .common import *
from .Signals import Signals

# chat_agent


class MyChatAgent(ChatAgent):
    """自定义聊天代理，实现流式响应"""

    def __init__(self, model, output_language="中文"):
        super().__init__(model=model, output_language=output_language)
        self._model = model
        self.result = []  # 记录流式响应结果

    def stream_response(self, prompt, id: int):
        """
        处理流式响应
        prompt (str): 用户输入的提示词
        """

        api_url = f"{self._model._url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._model._api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self._model.model_type,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "max_tokens": 2000,
            "temperature": 0.7,
        }

        try:
            with requests.post(
                api_url,
                headers=headers,
                json=data,
                stream=True,
                timeout=60,  # 设置超时时间
            ) as response:

                # 检查HTTP状态码
                if response.status_code != 200:
                    print(
                        f"Agent_1 API请求失败，状态码: {response.status_code}, 错误: {response.text}"
                    )
                    self.send_message(f"[ERROR] {error_msg}")
                    return

                for chunk in response.iter_lines():
                    if chunk:
                        chunk_str = chunk.decode("utf-8").strip()

                        # 跳过心跳和结束事件
                        if chunk_str == "[DONE]":
                            break

                        if chunk_str.startswith("data:"):
                            try:
                                chunk_data = json.loads(chunk_str[5:])  # 去掉 "data:"
                                if chunk_data==" [DONE]":
                                    break
                                content = (
                                    chunk_data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )

                                if content:
                                    self.send_message(content)

                            except json.JSONDecodeError as e:
                                print(
                                    f"Agent_1 JSON解析错误: {e}, 原始数据: {chunk_str}"
                                )
                                continue

        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            print(f"Agent_1 {error_msg}")
            self.send_message(f"[ERROR] {error_msg}")

        finally:
            self.send_result(id)

    def receive_message(self, message, id: int):
        """接收消息并触发流式响应"""
        print(f"Agent_1开始处理:{message};来自页面{id}")
        self.stream_response(message, id)

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
        self.result.clear()
