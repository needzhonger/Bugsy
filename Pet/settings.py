from PySide6.QtGui import QImage

current_img= None
previous_img= None

# 动画状态
act_id: int = 0  # 当前选中的动作ID
current_act = None  # 当前动作对象/数据
previous_act = None  # 上一个动作对象/数据

# 对话框状态
showing_dialogue_now: bool = False  # 当前是否正在显示对话框


def init():
    """
    初始化应用程序所需的全局状态变量。
    """
    global current_img, previous_img, onfloor, draging, set_fall, playid, mouseposx1, mouseposx2, mouseposx3, mouseposx4, mouseposx5, mouseposy1, mouseposy2, mouseposy3, mouseposy4, mouseposy5, dragspeedx, dragspeedy, fixdragspeedx, fixdragspeedy, fall_right, act_id, current_act, previous_act, showing_dialogue_now

    current_img = QImage()
    previous_img = QImage()

    # 动画相关
    act_id = 0  # 默认动作ID
    current_act = None
    previous_act = None

    # 对话框相关
    showing_dialogue_now = False  # 初始不显示对话框
