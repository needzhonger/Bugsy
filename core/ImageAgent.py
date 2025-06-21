from .common import *
from .Model import vision_model
from PIL import Image


class ImageAgent:
	"""图像识别"""

	def __init__(self, _model):
		self.model = _model
		self.chat_agent = ChatAgent(model=self.model, output_language='中文')

	def image_analysis(self, image, question):
		"""image是Image解析后的形式"""
		image_msg = BaseMessage(
			role_name="assistant",
			content=question,
			image_list=[image],  # 图片
			meta_dict={},
			role_type=RoleType.ASSISTANT
		)

		response = self.chat_agent.step(image_msg)

		if response and response.msgs:
			print_text_animated(response.msgs[0].content)
		else:
			print("未能获取到有效的回复。")
			if response and response.info:
				print(response.info)

	def receive_message(self, path, question):
		"""从前端接收信息"""
		# path是图片文件路径，question是问题
		image = Image.open(path)
		self.image_analysis(image, question)


if __name__ == "__main__":
	test_agent = ImageAgent(vision_model)
	while True:
		img = input("请输入图片路径（本地）\n")  # 发送的路径不能有引号，不需要用'\'转义
		question = input("请输入问题\n")
		test_agent.receive_message(img, question)
