from colorama import Fore
from pydantic import BaseModel
from .common import *
import json
from .Signals import Signals



class TestCase(BaseModel):
    input: str
    origin_output: str
    expected_output: str


class StructuredOutputSchema(BaseModel):
    problem_analysis: str
    error_reason: str
    correct_code: str
    test_cases: list[TestCase]


class StructuredAgent:
    def __init__(self, model):
        self.model = model
        self.result = []

    def receive_message(self, message, id: int):
        self.result = []
        """接收消息并触发流式响应"""
        print(f"Agent_2开始处理:{message};来自页面{id}")
        agent = ChatAgent(model=self.model)
        response = agent.step(message, response_format=StructuredOutputSchema)
        # 提取消息内容（注意：response.msg.content 才是实际文本）
        content = response.msg.content
        print("正在生成JSON文件\n")
        print("正在解析...\n")

        parsed = None
        try:
            if isinstance(content, dict):
                parsed = StructuredOutputSchema(**content)
            else:
                parsed = StructuredOutputSchema(**json.loads(content))
        except Exception as e:
            print("\n解析失败，请检查模型输出格式。")
            print("错误信息：", e)
            print("原始内容：", content)

        self.result.append(f"## 🧠 题目分析\n\n{parsed.problem_analysis}\n")
        self.result.append(f"\n---\n")
        self.result.append(f"## ❌ 错误原因\n\n{parsed.error_reason}\n")
        self.result.append(f"\n---\n")
        self.result.append(f"## ✅ 正确代码\n\n```python\n{parsed.correct_code}\n```\n")
        self.result.append(f"\n---\n")
        self.result.append(f"## 📊 测试数据\n")

        for i, case in enumerate(parsed.test_cases, 1):
            self.result.append(f"\n### 示例 {i}\n")
            self.result.append(f"- **输入：** `{case.input}`\n")
            self.result.append(f"- **原代码输出：** `{case.origin_output}`\n")
            self.result.append(f"- **期望输出：** `{case.expected_output}`\n")

        self.send_result(id)

    def send_result(self, id: int):
        print(f"Agent_2 向ChatWindow(id={id})发送结果")
        Signals.instance().send_debug_agent_response(self.result)
        self.result.clear()