from camel.models import ModelFactory
from camel.types import ModelPlatformType
from dotenv import load_dotenv
import os

# 加载 API Key
# load_dotenv(dotenv_path="API_KEY.env")
# API_KEY = os.getenv("API_KEY")
API_KEY = "sk-vuigflksccgkzuqiqjrjzchnnsydsxyxcbqoovxgdqejhuas"
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
