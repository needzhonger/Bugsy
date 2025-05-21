from common import *
from Signals import Signals

log = logging.getLogger(__name__)

load_dotenv(dotenv_path='../API_KEY.env')
api_key = os.getenv('API_KEY')


class MyChatAgent(ChatAgent):
	"""自定义类，实现流式响应"""

	def __init__(self, model, output_language="中文"):
		super().__init__(model=model, output_language=output_language)
		self._model = model

		log.info("MyChatAgent初始化完成")

	def stream_response(self, prompt):
		"""流式输出响应"""
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
		}

		with requests.post(api_url, headers=headers, json=data, stream=True) as response:
			for chunk in response.iter_lines():
				if chunk:
					chunk_str = chunk.decode("utf-8").strip()
					if chunk_str.startswith("data:"):
						try:
							chunk_data = json.loads(chunk_str[5:])  # 去掉 "data:"
							content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
							if content:
								self.send_message(content)
						except json.JSONDecodeError:
							pass

	def receive_message(self, message):
		self.stream_response(message)

	def send_message(self, message):
		Signals.instance().send_ai_response(message)


# 初始化模型
model = ModelFactory.create(
	model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
	model_type="Pro/deepseek-ai/DeepSeek-R1",
	url="https://api.siliconflow.cn",
	api_key=api_key,
	model_config_dict={"max_tokens": 2000, "stream": True}
)
