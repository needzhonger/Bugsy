# 需要下载的库(如果是新创建的conda环境)

## CAMEL-AI 本体

pip install camel-ai

## 图像处理（需配合多模态模型）

pip install pillow opencv-python

## 向量数据库(用于知识库检索增强(RAG))

pip install chromadb sentence-transformers

##

pip install sqlalchemy

##  

pip install pandas

## GUI

pip install PySide6

## 如果要连接本地模型(可选)

pip install ollama transformers torch

# CAMEL-AI的基本功能

### meta_dict的用途

	用途								示例值												  应用场景

任务上下文传递 {"task_id": "debug_001", "step": 3} 多轮对话中跟踪任务进度
控制生成行为 {"strict_mode": True, "code_lang": "python"} 指定代码生成的语言或严格检查
附加工具信息 {"tools": ["code_executor"], "allow_web": False} 声明智能体可用的工具或权限
调试信息 {"debug": {"timestamp": "2024-05-20", "source": "user_upload"}} 记录消息来源或处理日志

## 智能体(Agent)系统

CAMEL的核心是智能体系统，每个智能体都有：
角色(Role)：定义智能体的身份（如"代码专家"）
背景(Background)：提供上下文信息
目标(Goal)：明确智能体的任务

示例：创建一个代码专家智能体

```python
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.types import RoleType

code_agent = ChatAgent(
	BaseMessage(
		role_name="Code Expert",
		role_type=RoleType.ASSISTANT,
		content="你是一个专业的编程助手，擅长代码生成和错误修复",
		meta_dict={}  # 传递空字典作为默认值
	),
	# model_config=config
)
```

### RoleType

RoleType 是 CAMEL-AI 中用于区分智能体基础角色的枚举类，主要包含以下几种类型：
ASSISTANT：助手角色（如AI助手、导师、顾问等）
USER：用户角色（如学生、普通用户、需求提出者等）
DEFAULT：默认角色（未明确指定时的基础类型）
SYSTEM：系统角色（管理对话流程或系统级操作的智能体）
这些类型帮助框架理解智能体在对话中的基本定位。

## 任务规划

CAMEL允许你定义具体任务，并分配给智能体：

```python
from camel.agents import TaskSpecifyAgent
from camel.messages import BaseMessage
from camel.types import RoleType

# 创建一个任务细化(TaskSpecify)智能体实例,这个智能体专门用于将模糊的任务描述转化为具体、可执行的任务说明
# 相当于一个"需求分析师"，把用户模糊的需求转化为AI可执行的明确任务
task_specifier = TaskSpecifyAgent()

# 创建一个基础消息(BaseMessage)对象，用于承载任务信息
# 这是CAMEL-AI中消息传递的基本单元
task_msg = BaseMessage(
	role_name="Task Specifier",  # 指定发送此消息的智能体角色名称
	role_type=RoleType.ASSISTANT,  # 指定角色类型为ASSISTANT（助手）.注意：虽然这里用ASSISTANT，但TaskSpecifyAgent实际是"系统级"角色
	content="开发一个Python函数来计算斐波那契数列",  # 任务内容的原始描述（用户输入的模糊需求）
	meta_dict={}  # 传递空字典作为默认值
)

# 调用任务细化智能体的step方法处理任务消息
# step()是CAMEL中智能体执行动作的标准方法
# 这个过程会：
# 1. 将原始任务发送给AI模型（如GPT）
# 2. 要求模型输出更详细的任务说明
# 3. 返回包含细化结果的新消息
specified_task_msg = task_specifier.step(task_msg)

# 打印细化后的任务内容
# 输出示例可能类似：
# "编写一个Python函数fibonacci(n)，使用递归实现，要求：
#  1. 处理n<=0的情况返回空列表
#  2. 处理n=1返回[0]
#  3. 处理n=2返回[0,1]
#  4. 包含类型注解和docstring"
print(specified_task_msg.content)  # 输出是细化后的提示词
```

## 角色扮演：创建多个智能体进行对话

```python
from camel.societies import RolePlaying  # 导入RolePlaying类，这是CAMEL-AI框架中用于管理两个智能体对话的核心类
from camel.types import RoleType
from camel.messages import BaseMessage

# 创建两个角色进行对话

# 创建用户角色消息对象（学生角色）
# BaseMessage是CAMEL中所有消息交互的基础数据结构
user_agent = BaseMessage(
	role_name="Student",
	role_type=RoleType.USER,  # 用户角色
	content="我需要帮助解决Python代码问题",  # 角色初始内容 - 相当于该角色的"开场白"
	meta_dict={}
)

# 创建助手角色消息对象（编程导师角色）
assistant_agent = BaseMessage(
	role_name="Programming Tutor",
	role_type=RoleType.ASSISTANT,  # 提供服务的智能体
	content="我可以帮助你解决Python编程问题",  # 智能体的初始身份设定
	meta_dict={}
)

# 创建角色扮演会话实例
# 底层会执行：
# 1. 初始化两个ChatAgent实例
# 2. 建立消息交换通道
# 3. 设置对话终止条件等控制逻辑
session = RolePlaying(user_agent, assistant_agent)

# 1. 初始化对话（交换初始问候）
init_msg = session.init_chat()

# 2. 进行多轮对话
for _ in range(3):  # 假设进行3轮对话（不宜过长）
	user_response = session.step(session.assistant_agent)  # 老师发言 → 用户回应
	tutor_response = session.step(session.user_agent)  # 用户发言 → 老师回应
# print(f"{response.role_name}: {response.content}")

# 3. 获取完整对话历史
print(session.get_full_history())
```

## 与AI API集成(以Deepseek为例)

自定义Config:

```python
from camel.configs import BaseConfig
from typing import Optional
from camel.types import RoleType
from camel.messages import BaseMessage


class DeepSeekConfig(BaseConfig):
	"""自己定义类"""

	def __init__(
			self,
			model_name: str = "deepseek-coder-33b",
			api_key: Optional[str] = None,
			base_url: str = "https://api.deepseek.com/v1",
			temperature: float = 0.7,
	):
		super().__init__()  # TODO:是否需要传递参数

		self.model_name = model_name
		self.api_key = api_key
		self.base_url = base_url
		self.temperature = temperature


# 自定义模型配置
# from DeepSeekConfig import DeepSeekConfig
from camel.agents import ChatAgent

config = DeepSeekConfig(
	model_name="deepseek-coder-33b",
	api_key="your_deepseek_key"
)

agent = ChatAgent(
	BaseMessage(role_name="Code Assistant",
				role_type=RoleType.ASSISTANT,
				content="你是一个由DeepSeek驱动的代码专家",
				meta_dict={}  # 传递空字典作为默认值
				),
	model_config=config
)
```

## 处理复杂工作流

```python
from camel.agents import TaskPlannerAgent, TaskSpecifyAgent
from camel.messages import BaseMessage
from camel.types import RoleType

# 创建任务规划器
planner = TaskPlannerAgent()
task_specifier = TaskSpecifyAgent()

# 分解任务
planned_tasks = planner.step(
	BaseMessage(
		role_name="Planner",
		content="开发一个Python程序，从API获取数据，处理并存储到数据库",
		role_type=RoleType.ASSISTANT,
		meta_dict={}
	)
)

# 细化每个任务
specified_tasks = []
for task in planned_tasks:
	specified = task_specifier.step(task)
	specified_tasks.append(specified)
```