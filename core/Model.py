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

def decode(api_key):
    res = ""
    for i in api_key :
        res += chr(ord(i) - 3)
    return res
def init_models():
    api_key = load_api_key()
    api_key = decode(api_key)
    print(f"设置API_KEY为: {api_key}")

    _model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="Pro/deepseek-ai/DeepSeek-R1",
        url="https://api.siliconflow.cn",
        api_key=api_key,
        model_config_dict={"temperature": 0.5, "max_tokens": 10000, "stream": True},
    )

    _vision_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="Qwen/Qwen2.5-VL-72B-Instruct",
        url="https://api.siliconflow.cn",
        api_key=api_key,
        model_config_dict={"stream": True},
    )
    return _model, _vision_model

# 启动时初始化一次
model, vision_model = init_models()