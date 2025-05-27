# 需要下载的库(如果是新创建的conda环境)

#### CAMEL-AI

pip install camel-ai

#### 图像处理（需配合多模态模型）

pip install pillow opencv-python

#### 向量数据库(用于知识库检索增强(RAG))

pip install chromadb sentence-transformers

#### 管理密钥的库

pip install python-dotenv

#### 处理数据的库

pip install sqlalchemy

#### pandas

pip install pandas

#### 其它
pip install tinycss2
pip install markdown pygments bleach beautifulsoup4
# 搭建智能体

## 搭建一个模型（使用硅基流动API）


### 创建并进行一次对话

```python
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType

model = ModelFactory.create(
	model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
	model_type="Name",  # 模型名称写全名
	url="https://api.siliconflow.cn",  # 网址，写到cn即可
	api_key='api_key',  # 密钥
	model_config_dict={"max_tokens": 2000}  # 设置最大生成长度
)

# 将模型放进智能体
agent = ChatAgent(model=model,output_language='中文')

# 进行对话
response = agent.step("你好，你是谁？")  # 使用step()进行一次对话
print(response.msgs[0].content)
```

### 两个智能体对话

```python
from colorama import Fore
from camel.societies import RolePlaying
from camel.utils import print_text_animated
from camel.models import ModelFactory
from camel.types import ModelPlatformType

# 定义模型
model = ModelFactory.create(
	model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
	model_type="Name",
	url="https://api.siliconflow.cn",
	api_key="api_key",
	model_config_dict={"max_tokens": 10000}  # 设置最大生成长度
)


def communication(task_prompt, assistant_role_name, user_role_name, use_task_specify=False, model=model,
				  chat_turn_limit=10):
	"""
	RolePlaying功能：进行多轮自动的对话
	:param task_prompt: 任务目标
	:param assistant_role_name：AI助手角色名
	:param user_role_name：用户角色名
	:param model: 所用的模型
	:param use_task_specify:启用任务细化功能
	:param chat_turn_limit: 对话次数
	:return: None
	"""

	role_play_session = RolePlaying(
		assistant_role_name=assistant_role_name,  # 设置AI助手角色名
		assistant_agent_kwargs=dict(model=model),  # 设置AI助手角色名称
		user_role_name=user_role_name,  # 设置用户角色名，在roleplay中，user用于指导AI助手完成任务
		user_agent_kwargs=dict(model=model),  # 配置用户使用的模型
		task_prompt=task_prompt,  # 任务目标
		with_task_specify=use_task_specify,  # 是否启用任务细化功能
		task_specify_agent_kwargs=dict(model=model),  # 配置任务细化使用的模型
		output_language='中文',  # 设置输出语言
	)

	# AI 助手系统消息，展示AI助手在对话中遵循的底层指令（助手的角色定义、任务目标（如“帮助用户诊断病情”）、行为规范（如“用专业但易懂的语言回答”）、输出语言要求（如“用中文回答”））
	print(Fore.GREEN + f"AI 助手系统消息:\n{role_play_session.assistant_sys_msg}\n")
	# 展示模拟用户（AI扮演的“指导者”）的行为逻辑：用户的角色定义（如“你是……”）。用户的任务目标。交互规则（如“每次只提一个问题”）
	print(Fore.BLUE + f"AI 用户系统消息:\n{role_play_session.user_sys_msg}\n")
	# 原始任务提示：函数传入的 task_prompt 参数，即用户最初指定的任务描述（未经修改）
	print(Fore.YELLOW + f"原始任务提示:\n{task_prompt}\n")
	# 任务细化（Task Specify）后的版本(specified_task_prompt)
	print(Fore.CYAN + "指定的任务提示:" + f"\n{role_play_session.specified_task_prompt}\n")
	# 实际用于对话的最终任务提示（task_prompt），可能是：直接使用原始任务（如果未启用细化）;使用细化后的任务（如 with_task_specify=True 时）;经过额外调整的版本（如语言本地化后的任务）.
	print(Fore.RED + f"最终任务提示:\n{role_play_session.task_prompt}\n")

	# 开始对话
	input_msg = role_play_session.init_chat()  # 初始化input_msg
	for _ in range(chat_turn_limit):
		assistant_response, user_response = role_play_session.step(input_msg)  # 输入input_msg

		# 检查AI助手是否终止了对话
		if assistant_response.terminated:
			print(Fore.GREEN + "AI 助手已终止。原因: "f"{assistant_response.info['termination_reasons']}.")
			break
		# 检查用户是否终止了对话
		if user_response.terminated:
			print(Fore.GREEN + "AI 用户已终止。"f"原因: {user_response.info['termination_reasons']}.")
			break

		# 输出
		# 用户发言，流式响应
		print_text_animated(Fore.BLUE + f"AI 用户:\n{user_response.msg.content}\n")
		# AI发言，流式响应
		print_text_animated(Fore.GREEN + f"AI 助手:\n{assistant_response.msg.content}\n")

		# 检查用户是否表示任务完成(通过特定标记判断)
		if "CAMEL_TASK_DONE" in user_response.msg.content:
			break

		# 更新input_msg为AI助手的响应，因为下一轮用户会先发言
		input_msg = assistant_response.msg


while True:
	task_prompt = input("请输入任务\n")
	user_role_name = input("请输入用户角色")
	assistant_role_name = input("请输入AI助手角色")
	use_task_specify = True if input("是否使用任务细化功能:\ny:使用    n:不使用\n")=='y' else False
	communication(task_prompt, assistant_role_name, user_role_name, use_task_specify)
```