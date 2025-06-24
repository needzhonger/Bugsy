from camel.models import ModelFactory
from camel.types import ModelPlatformType
from dotenv import load_dotenv
import os

# 加载 API Key
# 获取当前脚本文件所在目录（也就是 core/）
script_dir = os.path.dirname(os.path.abspath(__file__))

# 拼接出 API_KEY.env 的绝对路径
env_path = os.path.join(script_dir, "API_KEY.env")

# 加载 .env 文件
load_dotenv(dotenv_path=env_path)
API_KEY = os.getenv("API_KEY")
print(f"API_KEY:{API_KEY}")

# 处理文本的模型
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    model_type="Pro/deepseek-ai/DeepSeek-R1",
    url="https://api.siliconflow.cn",
    api_key=API_KEY,
    model_config_dict={"temperature": 0.5, "max_tokens": 10000, "stream": True},
)

# 处理图片的模型
vision_model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    model_type="Qwen/Qwen2.5-VL-72B-Instruct",
    url="https://api.siliconflow.cn",
    api_key=API_KEY,
    model_config_dict={"stream": True},
)
