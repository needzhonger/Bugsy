from .common import *
from PIL import Image
from .Signals import Signals


class ImageWorker(QThread):
    result_ready = Signal(list)

    def __init__(self, model, image, question):
        super().__init__()
        self.model = model
        self.image = image
        self.question = question

    def run(self):
        chat_agent = ChatAgent(model=self.model, output_language="中文")
        result = []

        image_msg = BaseMessage(
            role_name="assistant",
            content=self.question,
            image_list=[self.image],
            meta_dict={},
            role_type=RoleType.ASSISTANT,
        )

        response = chat_agent.step(image_msg)

        if response and response.msgs:
            print(response.msgs[0].content)
            result.append(response.msgs[0].content)
        else:
            print("未能获取到有效的回复。")
            result.append("未能获取到有效的回复。")
            if response and response.info:
                print(response.info)
                result.append(response.info)

        self.result_ready.emit(result)


class ImageAgent:
    """图像识别"""

    def __init__(self, _model):
        self.model = _model
        self.chat_agent = ChatAgent(model=self.model, output_language="中文")
        self.result = []

    def change_model(self, new_model):
        self.model = new_model
        self.chat_agent = ChatAgent(model=self.model, output_language="中文")
        self.result = []

    def image_analysis(self, image, question):
        """image是Image解析后的形式"""
        self.worker = ImageWorker(self.model, image, question)
        self.worker.result_ready.connect(lambda x: self.send_result(x))
        self.worker.start()

    def receive_message(self, img, question):
        """从前端接收信息"""
        print(f"ImageAgent开始处理:图片地址:{img};问题:{question}")
        image = Image.open(img)
        self.image_analysis(image, question)

    def send_result(self, result):
        print("ImageAgent向ChatWindow发送结果")
        Signals.instance().send_image_agent_response(result)


# 用法示例:
# test_agent = ImageAgent(vision_model)
# while True:
#     img = input("请输入图片路径（本地）\n")  # 发送的路径不能有引号，不需要用'\'转义
#     question = input("请输入问题\n")
#     test_agent.receive_message(img, question)
