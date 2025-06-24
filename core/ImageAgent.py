from .common import *
from PIL import Image
from .Signals import Signals


class ImageAgent:
    """图像识别"""

    def __init__(self, _model):
        self.model = _model
        self.chat_agent = ChatAgent(model=self.model, output_language="中文")
        self.result = []

    def image_analysis(self, image, question):
        """image是Image解析后的形式"""
        image_msg = BaseMessage(
            role_name="assistant",
            content=question,
            image_list=[image],  # 图片
            meta_dict={},
            role_type=RoleType.ASSISTANT,
        )

        response = self.chat_agent.step(image_msg)

        if response and response.msgs:
            self.result.append(response.msgs[0].content)
        else:
            self.result.append("未能获取到有效的回复。")
            if response and response.info:
                self.result.append(response.info)

        self.send_result()

    def receive_message(self, img, question):
        """从前端接收信息"""
        image = Image.open(img)
        print(f"ImageAgent开始处理:图片尺寸:{image.size};问题:{question}")
        self.image_analysis(image, question)

    def send_result(self):
        print("ImageAgent向ChatWindow发送结果")
        Signals.instance().send_image_agent_response(self.result)
        self.result.clear()


# 用法示例:
# test_agent = ImageAgent(vision_model)
# while True:
#     img = input("请输入图片路径（本地）\n")  # 发送的路径不能有引号，不需要用'\'转义
#     question = input("请输入问题\n")
#     test_agent.receive_message(img, question)
