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


class StructuredAgentThread(QThread):
    result_ready = Signal(list, int)  # (result, id)

    def __init__(self, model, message, id):
        super().__init__()
        self.model = model
        self.message = message
        self.id = id

    def run(self):
        result = []
        print(f"[线程] Agent_2开始处理: {self.message}; 来自页面{self.id}")
        agent = ChatAgent(model=self.model)
        response = agent.step(self.message, response_format=StructuredOutputSchema)
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
            return  # 不发信号，直接退出线程

        result.append(f"## 🧠 题目分析\n\n{parsed.problem_analysis}\n")
        result.append(f"\n---\n")
        result.append(f"## ❌ 错误原因\n\n{parsed.error_reason}\n")
        result.append(f"\n---\n")
        result.append(f"## ✅ 正确代码\n\n```python\n{parsed.correct_code}\n```\n")
        result.append(f"\n---\n")
        result.append(f"## 📊 测试数据\n")

        for i, case in enumerate(parsed.test_cases, 1):
            result.append(f"\n### 示例 {i}\n")
            result.append(f"- **输入：** `{case.input}`\n")
            result.append(f"- **原代码输出：** `{case.origin_output}`\n")
            result.append(f"- **期望输出：** `{case.expected_output}`\n")

        self.result_ready.emit(result, self.id)


class StructuredAgent:
    def __init__(self, model):
        self.model = model
        self.result = []
        self.worker_thread = None

    def receive_message(self, message, id: int):
        self.result = []
        self.worker_thread = StructuredAgentThread(self.model, message, id)
        self.worker_thread.result_ready.connect(self.send_result)
        self.worker_thread.start()

    def send_result(self, result: list[str], id: int):
        print(f"[主线程] Agent_2 向ChatWindow(id={id})发送结果")
        self.result = result
        Signals.instance().send_debug_agent_response(self.result)
        self.result.clear()