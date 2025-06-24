from colorama import Fore
from camel.societies import RolePlaying
from camel.utils import print_text_animated
from pydantic import BaseModel
from .Model import model
from .common import *
import json



class TestCase(BaseModel):
    input: str
    origin_output: str
    expected_output: str


class StructuredOutputSchema(BaseModel):
    problem_analysis: str
    error_reason: str
    correct_code: str
    test_cases: list[TestCase]


class AIAgent:
    def __init__(self, model):
        self.model = model

    def change_model(self, new_model):
        self._model = new_model

    def communication(
        self,
        task_prompt,
        assistant_role_name,
        user_role_name,
        use_task_specify=False,
        chat_turn_limit=10,
    ):
        role_play_session = RolePlaying(
            assistant_role_name=assistant_role_name,
            assistant_agent_kwargs=dict(model=self.model),
            user_role_name=user_role_name,
            user_agent_kwargs=dict(model=self.model),
            task_prompt=task_prompt,
            with_task_specify=use_task_specify,
            task_specify_agent_kwargs=dict(model=self.model),
            output_language="中文",
        )

        print(Fore.GREEN + f"AI 助手系统消息:\n{role_play_session.assistant_sys_msg}\n")
        print(Fore.BLUE + f"AI 用户系统消息:\n{role_play_session.user_sys_msg}\n")
        print(Fore.YELLOW + f"原始任务提示:\n{task_prompt}\n")
        print(
            Fore.CYAN
            + "指定的任务提示:"
            + f"\n{role_play_session.specified_task_prompt}\n"
        )
        print(Fore.RED + f"最终任务提示:\n{role_play_session.task_prompt}\n")

        input_msg = role_play_session.init_chat()
        for _ in range(chat_turn_limit):
            assistant_response, user_response = role_play_session.step(input_msg)

            if assistant_response.terminated:
                print(
                    Fore.GREEN + "AI 助手已终止。原因: "
                    f"{assistant_response.info['termination_reasons']}."
                )
                break
            if user_response.terminated:
                print(
                    Fore.GREEN + "AI 用户已终止。"
                    f"原因: {user_response.info['termination_reasons']}."
                )
                break

            # 用户发言，流式响应
            print_text_animated(
                Fore.BLUE + f"AI 用户:\n\n{user_response.msg.content}\n"
            )
            # AI发言，流式响应
            print_text_animated(
                Fore.GREEN + "AI 助手:\n\n" f"{assistant_response.msg.content}\n"
            )

            if "CAMEL_TASK_DONE" in user_response.msg.content:
                print("任务完成！")
                break

            input_msg = assistant_response.msg

    def structured_output(
        self, problem_description: str, code_lang: str, user_code: str
    ):
        prompt = f"""
我正在做如下{code_lang}编程题：

{problem_description}

以下是我写的代码：

{user_code}

请按以下四个方面分析并输出：
1. 对题目的分析
2. 我的错误代码的问题
3. 正确的代码
4. 两组测试数据（含输入、原代码输出和期望输出）
"""
        agent = ChatAgent(model=self.model)
        response = agent.step(prompt, response_format=StructuredOutputSchema)
        # 提取消息内容（注意：response.msg.content 才是实际文本）
        content = response.msg.content
        print_text_animated(Fore.BLUE + f"正在生成JSON文件\n")
        print_text_animated(Fore.RED + "正在解析...\n")

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
        return parsed


if __name__ == "__main__":
    agent = AIAgent(model)

    while True:
        problem_description = input(Fore.BLACK + "请输入题目描述：\n")
        code_lang = input(Fore.BLACK + "请输入编程语言：（cpp、python、java等）\n")
        user_code = input(
            Fore.BLACK + "请输入错误代码：(由于输入格式限制，请在一行内输入)\n"
        )
        output = agent.structured_output(problem_description, code_lang, user_code)
        print_text_animated(Fore.GREEN + f"【题目分析】\n{output.problem_analysis}\n")
        print_text_animated(Fore.GREEN + f"【错误原因】\n{output.error_reason}\n")
        print_text_animated(Fore.YELLOW + f"【正确代码】\n{output.correct_code}\n")
        print_text_animated(Fore.BLUE + f"【测试数据】\n")

        for i, case in enumerate(output.test_cases, 1):
            print_text_animated(
                Fore.BLUE
                + f"示例{i}：\n输入: {case.input}\n原代码输出: {case.origin_output}\n期望输出: {case.expected_output}\n\n"
            )
