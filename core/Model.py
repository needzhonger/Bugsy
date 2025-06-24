from camel.models import ModelFactory
from camel.types import ModelPlatformType
from dotenv import load_dotenv
import os

# 获取当前脚本目录（core/）
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, "API_KEY.env")

# 初始化全局模型变量
model = None
vision_model = None

def load_api_key():
    load_dotenv(dotenv_path=env_path, override=True)
    return os.getenv("API_KEY")

def init_models():
    global model, vision_model

    api_key = load_api_key()
    print(f"当前API_KEY: {api_key}")

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="Pro/deepseek-ai/DeepSeek-R1",
        url="https://api.siliconflow.cn",
        api_key=api_key,
        model_config_dict={"temperature": 0.5, "max_tokens": 10000, "stream": True},
    )

    vision_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="Qwen/Qwen2.5-VL-72B-Instruct",
        url="https://api.siliconflow.cn",
        api_key=api_key,
        model_config_dict={"stream": True},
    )

# 启动时初始化一次
init_models()