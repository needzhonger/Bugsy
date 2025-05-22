import time
import random
from random import choice
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QObject, QPoint
from PySide6.QtGui import QImage, QPixmap, QIcon, QCursor
from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, QThread, Signal

from typing import List, Optional

from Pet.utils import *
from Pet.conf import *

import Pet.settings as settings


class AnimationWorker(QObject):
    """
    动画处理工作线程类。
    负责根据宠物配置随机播放动画，并在独立的线程中运行。
    通过信号与主线程（通常是UI线程）通信以更新图像和位置。
    """

    # --- 信号定义 ---
    sig_set_img_anim = Signal(name='sig_set_img_anim')  # 请求设置新图像的信号
    sig_move_anim = Signal(
        float, float, name='sig_move_anim'
    )  # 请求移动宠物的信号 (dx, dy)
    sig_repaint_anim = Signal(name='sig_repaint_anim')  # 请求重绘的信号

    def __init__(self, pet_conf: PetConfig, parent: Optional[QObject] = None) -> None:
        """
        初始化动画工作线程。
        """
        super(AnimationWorker, self).__init__(parent)
        self.pet_conf: PetConfig = pet_conf
        self.is_killed: bool = False  # 线程是否被标记为终止
        self.is_paused: bool = False  # 线程是否被标记为暂停

    def run(self) -> None:
        """
        线程主循环。
        持续运行，直到 is_killed 被设置为 True。
        循环执行随机动作，处理暂停状态，并按配置的刷新率休眠。
        """
        print(f'开始运行宠物 {self.pet_conf.petname} 的动画线程')
        while not self.is_killed:
            # 执行一个随机选择的动作序列
            self.random_act()

            # 检查是否需要暂停或已终止
            if self._check_pause_kill():
                break  # 如果在暂停期间被终止，则退出循环

            # 如果没有被终止，则按配置的间隔休眠
            if not self.is_killed:
                time.sleep(self.pet_conf.refresh)

        print(f'宠物 {self.pet_conf.petname} 的动画线程已停止')

    def kill(self) -> None:
        """标记线程为终止状态，并确保其不处于暂停状态。"""
        self.is_paused = False  # 确保解除暂停状态，以便线程能检查 is_killed
        self.is_killed = True

    def pause(self) -> None:
        """标记线程为暂停状态。"""
        self.is_paused = True

    def resume(self) -> None:
        """解除线程的暂停状态。"""
        self.is_paused = False

    def _check_pause_kill(self) -> bool:
        """
        私有辅助方法：检查并处理暂停状态。
        如果线程被暂停，则循环等待直到恢复或被终止。
        """
        while self.is_paused:
            if self.is_killed:  # 在暂停期间也检查终止标记
                return True
            time.sleep(0.2)  # 暂停时短暂休眠，避免CPU空转
        return self.is_killed  # 返回当前的终止状态

    def random_act(self) -> None:
        """
        随机选择并执行一个动作序列。
        根据 pet_conf 中定义的动作概率分布来选择动作。
        """

        # 根据概率分布选择动作索引
        prob_num = random.uniform(0, 1)
        # 计算累积概率，找到第一个大于 prob_num 的区间的索引
        act_index = sum(
            int(prob_num > self.pet_conf.act_prob[i])
            for i in range(len(self.pet_conf.act_prob))
        )

        # 获取选中的动作序列 (可能包含一个或多个动作 Act)
        acts: List[Act] = self.pet_conf.random_act[act_index]

        # 执行选中的动作序列
        self._run_acts(acts)

    def _run_acts(self, acts: List[Act]) -> None:
        """
        按顺序执行一个动作序列中的所有单个动作 (Act)。
        """
        for act in acts:
            if self.is_killed:  # 在每个动作开始前检查终止状态
                break
            self._run_act(act)

    def _run_act(self, act: Act) -> None:
        """
        执行单个动作 (Act) 的动画。
        循环播放该动作的所有帧图像，并在每帧之间处理移动、暂停和休眠。
        """
        # 一个动作可能重复执行多次 (act.act_num)
        for _ in range(act.act_num):
            if self._check_pause_kill():
                return  # 检查暂停/终止，如果终止则直接返回

            # 遍历动作中的每一帧图像
            for img in act.images:
                if self._check_pause_kill():
                    return  # 检查暂停/终止，如果终止则直接返回

                # --- 更新图像 ---
                # 注意：直接修改全局 settings 模块中的图像变量
                settings.previous_img = settings.current_img
                settings.current_img = img
                self.sig_set_img_anim.emit()  # 发送信号，请求UI更新图像

                # --- 帧间延迟 ---
                time.sleep(act.frame_refresh)

                self._move(act)  # 总是尝试根据动作信息移动

                # --- 请求重绘 ---
                self.sig_repaint_anim.emit()  # 发送信号，请求UI重绘

    def _static_act(self, pos: QPoint) -> None:
        """
        静态动作的位置判断。 - 目前舍弃不用
        用于确保宠物停留在屏幕边界内。
        """
        # 获取主屏幕的几何信息
        screen = QApplication.primaryScreen()
        if not screen:
            print("错误：无法获取主屏幕信息。")
            return
        screen_geo = screen.geometry()
        screen_width = screen_geo.width()
        screen_height = screen_geo.height()

        # 使用配置中的尺寸作为边界判断依据
        border_x = self.pet_conf.size[0]
        border_y = self.pet_conf.size[1]

        new_x = pos.x()
        new_y = pos.y()

        # 简单的边界碰撞检查
        if pos.x() < border_x:
            new_x = screen_width - border_x
        elif pos.x() > screen_width - border_x:
            new_x = border_x

        if pos.y() < border_y:
            new_y = screen_height - border_y
        elif pos.y() > screen_height - border_y:
            new_y = border_y

        # 如果位置需要调整，则发送移动信号
        if new_x != pos.x() or new_y != pos.y():
            # 计算相对移动量
            dx = new_x - pos.x()
            dy = new_y - pos.y()
            self.sig_move_anim.emit(float(dx), float(dy))

    def _move(self, act: Act) -> None:
        """
        根据动作信息计算位移量，并发出移动信号。
        """
        plus_x: float = 0.0
        plus_y: float = 0.0
        direction = act.direction  # 获取动作定义的方向

        if direction:  # 仅当方向有效时才计算位移
            move_amount = float(act.frame_move)  # 每帧的移动量
            if direction == 'right':
                plus_x = move_amount
            elif direction == 'left':
                plus_x = -move_amount
            elif direction == 'up':
                plus_y = -move_amount
            elif direction == 'down':
                plus_y = move_amount
        # 仅当有实际位移时才发出信号（可选优化）
        if plus_x != 0.0 or plus_y != 0.0:
            self.sig_move_anim.emit(plus_x, plus_y)  # 发送移动信号 (dx, dy)


import math

# 导入 PyQt5 相关模块
from PySide6.QtCore import QObject, QTimer, Signal, QPoint
from PySide6.QtGui import QPixmap

# 导入自定义的设置和动作类 (假定存在)
# from Pet import settings, QAction # QAction 可能与 PyQt5.QtWidgets.QAction 冲突，需确认其来源
# 假设 settings 是一个可全局访问的配置/状态对象
# 假设 QAction 是一个描述宠物动作的自定义类

# --- 全局变量/状态 (假设存在于 settings 模块) ---
# settings.current_act: 当前动作对象
# settings.previous_act: 上一个动作对象
# settings.playid: 当前动作帧的播放索引
# settings.current_img: 当前显示的图像 (QPixmap)
# settings.previous_img: 上一个显示的图像 (QPixmap)
# settings.act_id: 在一个动画序列中，当前执行到第几个动作 (Action) 的索引
# settings.draging: 标志位，表示是否正在被鼠标拖拽 (1 表示是, 0 表示否)
# settings.onfloor: 标志位，表示宠物是否在地面上 (1 表示是, 0 表示否)
# settings.set_fall: 标志位，表示是否启用了掉落行为 (1 表示启用, 0 表示禁用)
# settings.fall_right: 标志位，表示掉落时图像是否需要水平镜像
# settings.dragspeedx: x 轴拖拽/掉落速度
# settings.dragspeedy: y 轴拖拽/掉落速度


class Interaction_worker(QObject):
    """
    处理宠物交互逻辑的工作类。
    通常在单独的线程中运行，通过信号与主界面通信。
    """

    # --- 信号定义 ---
    sig_set_img_inter = Signal(name='sig_set_img_inter')
    sig_move_inter = Signal(float, float, name='sig_move_inter')
    sig_act_finished = Signal()


    def __init__(self, pet_conf, parent=None):
        """
        初始化 Interaction_worker。
        """
        super(Interaction_worker, self).__init__(parent)

        self.pet_conf = pet_conf
        self.is_killed = False
        self.is_paused = False
        self.interact = None
        # 注意: 每次将 act_name 设为 None 时，应重置 settings.playid 为 0
        self.act_name = None

        # 创建定时器，用于周期性地执行 run 方法
        self.timer = QTimer()
        # 连接定时器的 timeout 信号到 run 方法
        self.timer.timeout.connect(self.run)
        # 启动定时器，间隔时间由宠物配置中的 interact_speed 决定 (毫秒)
        self.timer.start(int(self.pet_conf.interact_speed))

    def run(self):
        """
                定时器触发时执行的核心方法。
                根据 self.interact 的值调用相应的处理函数。
                """
        # 如果当前没有指定交互方法，则直接返回
        if self.interact is None:
            return
        # 如果指定的交互方法名不是当前对象的有效方法名，则清空交互方法名并返回
        elif self.interact not in dir(self):
            self.interact = None
        # 否则，获取并执行对应的交互方法
        else:
            # 使用 getattr 获取名称为 self.interact 的方法，并传入 self.act_name 作为参数执行
            getattr(self, self.interact)(self.act_name)

    def start_interact(self, interact, act_name=None):
        """
        设置当前要执行的交互及其关联的动作名称。
        """
        # print("in start_interact!")
        # 设置当前交互方法名
        self.interact = interact
        # 设置当前动作名
        self.act_name = act_name

    def kill(self):
        """
        停止工作线程的活动并准备退出。
        """
        # 清除暂停状态
        self.is_paused = False
        # 设置终止标志
        self.is_killed = True
        # 停止定时器
        self.timer.stop()

    def pause(self):
        """
        暂停工作线程的活动。
        """
        # 设置暂停标志
        self.is_paused = True# 停止定时器，阻止 run 方法被调用
        self.timer.stop()


    def resume(self):
        """
        恢复工作线程的活动 (如果之前被暂停)。
        注意：此方法仅清除暂停标志，需要外部逻辑或修改来重新启动定时器。
        当前代码下，调用 resume 后，需要再次调用 self.timer.start() 才能恢复 run 的执行。
        """
        # 清除暂停标志
        self.is_paused = False

    def img_from_act(self, act):
        """
        根据给定的动作(act)对象，计算并设置当前应该显示的图像帧。
        处理动画帧的重复播放逻辑，并更新全局状态 (settings)。
        """

        # 如果当前动作发生变化
        if settings.current_act != act:
            # 将之前的当前动作存为上一个动作
            settings.previous_act = settings.current_act
            # 更新当前动作
            settings.current_act = act
            # 重置当前动作的播放帧索引
            settings.playid = 0

        # 计算每张图片需要重复显示的次数 (基于动作帧刷新率和 InteractionWorker 的更新速度)
        # math.ceil 确保至少重复一次
        n_repeat = math.ceil(act.frame_refresh / (self.pet_conf.interact_speed / 1000))
        # 创建一个扩展的图像列表，其中每个图像根据 n_repeat 重复，整个序列根据 act.act_num 重复
        img_list_expand = [
            item for item in act.images for i in range(n_repeat)
        ] * act.act_num
        # 从扩展列表中获取当前 playid 对应的图像
        img = img_list_expand[settings.playid]

        # 播放索引加 1
        settings.playid += 1
        # 如果播放索引超出了扩展列表的长度，则重置为 0，实现循环播放
        if settings.playid >= len(img_list_expand):
            settings.playid = 0

        # 更新上一帧图像
        settings.previous_img = settings.current_img
        # 更新当前帧图像
        settings.current_img = img

    def animat(self, act_name):
        """
        执行一个指定的动画序列。
        动画序列由 pet_conf.random_act 中的多个动作(act)对象组成。
        """
        # 在宠物配置的随机动作名称列表中找到 act_name 的索引
        # print("in Animate")
        acts_index = self.pet_conf.random_act_name.index(act_name)
        # 获取对应的动画序列 (一个包含多个动作对象的列表)
        acts = self.pet_conf.random_act[acts_index]

        # 检查当前动作序列的索引 (settings.act_id) 是否已超出序列长度
        if settings.act_id >= len(acts):
            # 如果动画序列播放完毕，重置动作序列索引
            settings.act_id = 0
            # 清除当前交互方法名，停止 animat 的后续调用
            self.interact = None
            # 发出动作完成信号
            self.sig_act_finished.emit()
        else:
            # 获取当前要执行的动作对象
            act = acts[settings.act_id]
            # 计算当前动作需要执行的总帧数 (考虑图像重复和动作次数)
            n_repeat = math.ceil(
                act.frame_refresh / (self.pet_conf.interact_speed / 1000)
            )
            n_repeat *= len(act.images) * act.act_num

            # 计算并设置当前帧图像
            self.img_from_act(act)

            if settings.playid >= n_repeat - 1:
                # 增加动作序列索引，准备执行下一个动作
                settings.act_id += 1

            # 如果计算出的当前图像与上一帧不同，则需要更新显示和移动
            if settings.previous_img != settings.current_img:
                # 发出设置图像信号
                # print("发送设置图像信号")
                self.sig_set_img_inter.emit()
                # 根据当前动作的定义进行移动
                self._move(act)

    def mousedrag(self, act_name):
        pass

    def drop(self):
        pass

    def _move(self, act) -> None:
        """
        根据动作(act)对象中定义的方和移动量，计算并发出移动信号。
        """

        # 初始化 x, y 轴位移量
        plus_x = 0.0
        plus_y = 0.0
        # 获取动作定义的方向
        direction = act.direction

        # 如果动作没有定义方向，则不移动
        if direction is None:
            pass
        # 根据方向字符串设置相应的位移量
        else:
            if direction == 'right':
                plus_x = act.frame_move
            elif direction == 'left':
                plus_x = -act.frame_move
            elif direction == 'up':
                plus_y = -act.frame_move
            elif direction == 'down':
                plus_y = act.frame_move

        # 发出移动信号，请求主界面移动宠物
        self.sig_move_inter.emit(plus_x, plus_y)


class Scheduler_worker(QObject):
    """
    调度器工作类，用于管理定时任务，如状态变化、番茄钟、专注模式和提醒事项。
    通常在单独的线程中运行，通过信号与主界面或其他组件通信。
    """

    # --- 信号定义 ---
    # 请求设置显示的对话文本 (文本内容)
    sig_settext_sche = Signal(str, name='sig_settext_sche')
    # 请求设置宠物的动作 (动作名称)
    sig_setact_sche = Signal(str, name='sig_setact_sche')
    # 请求设置宠物的状态值 (状态名称, 变化量)
    sig_setstat_sche = Signal(str, int, name='sig_setstat_sche')
    # 通知专注模式已结束
    sig_focus_end = Signal(name='sig_focus_end')
    # 通知番茄钟（系列）已结束或需要用户交互（如处理冲突）
    sig_tomato_end = Signal(name='sig_tomato_end')
    # 请求设置时间显示 (时间类型标识, 剩余时间/数值)
    sig_settime_sche = Signal(str, int, name='sig_settime_sche')

    # _get_city_from_gaode 方法将被完全删除
    # (下面的空行代表原方法位置，将被删除)

    def __init__(self, pet_conf, parent=None):
        """
        初始化 Scheduler_worker。
        """
        super(Scheduler_worker, self).__init__(parent)
        # 保存宠物配置对象的引用
        self.pet_conf = pet_conf

        self.is_killed = False
        self.is_paused = False

        self.words = []


    def run(self):
        """
        工作线程的入口点。
        """
        now_time = datetime.now().hour
        self.show_dialogue([self.greeting(now_time)])
        time.sleep(10)  # 注意：sleep 在子线程中是安全的

        self.words = [
            "我闻到了bug的味道，让我瞧瞧是哪行代码不听话",
            "Bugsy探长🕵️‍♂️正在出动，目标：把bug一锅端🍲！",
            "Bug不可怕，Bugsy在就不怕",
            "嘿嘿，被我抓到了吧!bug就藏在这行后面📍！",
            "呜呜……找了一圈没看到😢，是不是bug藏得太好了？",
            "别急别急📦，Bugsy正在翻找debug工具箱🔧",
            "哪怕一整天都在调bug，我们也要开心地过呦🍬",
            "今天风好舒服，好适合……不干活🌬️",
            "🌀汪呜……Bugsy的脑袋打结了，好多Bug要爆炸啦……"
        ]

        while not self.is_killed:
            # print("in scheduler run!")
            if not self.is_paused:
                # print("in show_dialogue!")
                self.show_dialogue([choice(self.words)])
            time.sleep(10)  # 注意：sleep 在子线程中是安全的

    def kill(self):
        """
        停止工作线程的活动并关闭调度器。
        """
        # 清除暂停状态
        self.is_paused = False
        # 设置终止标志
        self.is_killed = True

    def pause(self):
        """
        暂停调度器的活动。
        """
        # 设置暂停标志
        self.is_paused = True

    def resume(self):
        """
        恢复调度器的活动。
        """
        # 清除暂停标志
        self.is_paused = False

    def greeting(self, time):
        """
        根据给定的小时数返回相应的问候语。
        """
        base_greeting = ''
        if 0 <= time <= 10:
            base_greeting = '早上好!'
        elif 11 <= time <= 12:
            base_greeting = '中午好!'
        elif 13 <= time <= 17:
            base_greeting = '下午好！'
        elif 18 <= time <= 24:
            base_greeting = '晚上好!'
        else:
            base_greeting = '你好!'  # 默认问候语，以防时间无效或未覆盖的情况

        return f"{base_greeting} ,我是你的智能Debug助手Bugsy😊"

    def show_dialogue(self, texts_toshow=[]):
        """
        依次显示一系列对话文本。
        使用全局标志位 `settings.showing_dialogue_now` 实现简单的排队机制，
        避免同时显示多个对话框造成混乱。
        """
        # 等待：如果当前已有对话框在显示，则循环等待
        while settings.showing_dialogue_now:
            time.sleep(1)  # 等待1秒再检查
        # 标记：设置全局标志，表示现在开始显示对话框
        settings.showing_dialogue_now = True

        # 遍历要显示的文本列表
        for text_toshow in texts_toshow:
            # 发出信号，请求主界面显示当前文本
            # print("signal emitted")
            self.sig_settext_sche.emit(text_toshow)
            # 等待：让文本显示一段时间 (固定3秒)
            time.sleep(5)

        # 完成：所有文本显示完毕后，发出信号请求清除文本显示
        self.sig_settext_sche.emit('None')  # 'None' 作为清除文本的约定信号
        # 标记：清除全局标志，允许其他对话请求
        settings.showing_dialogue_now = False

    def add_tomato(self, n_tomato=None):
        pass

    def run_tomato(self, task_text):
        pass

    def cancel_tomato(self):
        pass

    def change_hp(self):
        pass

    def change_em(self):
        pass

    def change_tomato(self):
        pass

    def change_focus(self):
        pass

    def add_focus(self, time_range=None, time_point=None):
        pass

    def run_focus(self, task_text):
        pass

    def cancel_focus(self):
        pass

    def add_remind(self, texts, time_range=None, time_point=None, repeat=False):
        pass

    def run_remind(self, task_text):
        pass
