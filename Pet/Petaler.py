# -*- coding: utf-8 -*-
"""
Pet 核心 UI 模块 - Pet.py
"""
import os
import sys
import ctypes
from PySide6.QtCore import QRect, QThread
from PySide6.QtGui import QAction, QGuiApplication, QFont, QFontDatabase, QIcon, QCursor

from Pet.modules import *
from Pet.utils import *
from Pet.conf import *
import Pet.settings as settings
from core import run_Main_Window as buggy

settings.init()

# 修改 screen_scale 的获取方式
if sys.platform == "win32":
    try:
        screen_scale = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0
    except (AttributeError, OSError):
        screen_scale = 1.0
        print("警告：无法在Windows上获取屏幕缩放比例，将使用默认值 1.0")
else:
    # 对于非Windows平台 (如 macOS), 初始默认值设为 1.0。
    # Qt的AA_EnableHighDpiScaling会处理实际缩放。
    screen_scale = 1.0
    # 你也可以尝试通过Qt获取:
    # if QApplication.instance(): # 确保app实例已存在
    #     primary_screen = QApplication.primaryScreen()
    #     if primary_screen:
    #         screen_scale = primary_screen.devicePixelRatio()


class PetWidget(QWidget):

    def __init__(
        self, parent: Optional[QWidget] = None, curr_pet_name: str = '', pets: tuple = (), App = None
    ):
        """
        初始化宠物窗口部件。

        Args:
            parent: 可选的父窗口部件。默认为 None。
            curr_pet_name: 初始化时要加载的宠物名称。
                           如果为空字符串，则尝试使用 'pets' 元组中的第一个名称。
            pets: 包含所有可用宠物名称的元组 (例如, ('pet1', 'pet2'))。
            App: 传递app
        """
        super().__init__(parent, Qt.WindowType())

        # --- 安全性检查：确保有宠物可加载 ---
        if not curr_pet_name and not pets:
            raise ValueError(
                "必须提供 'curr_pet_name' 或非空的 'pets' 元组来初始化 PetWidget。"
            )

        # --- 核心数据属性初始化 ---
        self.App = App
        self.pets: tuple = pets  # 存储所有可用宠物的名称元组
        self.curr_pet_name: str = ''  # 当前激活的宠物名称 (将在 init_conf 中设置)
        self.pet_conf: PetConfig = (
            PetConfig()
        )  # 宠物配置对象 (将在 init_conf 中加载实际配置)

        self.image: Optional[QImage] = None  # 当前用于显示的 QImage 对象
        self.tray: Optional[QSystemTrayIcon]= None  # 系统托盘图标实例

        # --- 窗口交互状态属性 ---
        self.is_follow_mouse: bool = False  # 标志位：窗口当前是否跟随鼠标拖动
        self.mouse_drag_pos: QPoint = self.pos()  # 鼠标按下时相对于窗口左上角的偏移量

        # 获取屏幕尺寸，用于计算窗口边界等
        self.screen_geo: QRect = QGuiApplication.primaryScreen().geometry()  # QRect 对象
        self.screen_width: int = self.screen_geo.width()
        self.screen_height: int = self.screen_geo.height()

        # --- 初始化UI元素和窗口基础设置 ---
        self._init_ui()  # 创建UI元素 (QLabel, QProgressBar 等)
        self._init_widget()  # 设置窗口属性 (无边框, 总在最前, 背景透明等)

        # --- 加载指定的宠物配置 ---
        # 如果未直接指定当前宠物名称，则使用 pets 列表中的第一个
        initial_pet_name_to_load = curr_pet_name if curr_pet_name else pets[0]
        self.init_conf(initial_pet_name_to_load)  # 加载配置、图片字典、宠物数据等

        # --- 显示窗口 ---
        self.show()

        # --- 后台任务管理初始化 ---
        self.threads: dict[str, QThread] = {}  # 用于管理后台任务的线程对象
        self.workers: dict[str, QObject] = {}  # 用于管理后台任务的工作器对象

        # --- 启动核心后台任务 ---
        self.run_animation()  # 启动动画播放与随机行为线程
        self.run_interaction()  # 启动用户交互（如拖拽）响应线程
        self.run_scheduler()  # 启动计划任务（提醒、番茄钟等）线程

        # --- 根据加载的宠物数据配置UI ---
        self._setup_ui(self.pic_dict)  # 设置UI元素尺寸、初始值等

        self._right_menu_connected = False # 判断是否连接的标识符
    # 在 PetWidget 类定义内部

    def mousePressEvent(self, event) -> None:
        """
        处理鼠标按钮按下事件。

        根据按下的按钮执行不同操作：
        - 右键：准备并显示上下文菜单。
        - 左键：启动窗口拖动逻辑。
        """
        button = event.button()  # 获取按下的按钮

        # --- 处理鼠标右键点击 ---
        if button == Qt.MouseButton.RightButton:
            # 设置窗口的上下文菜单策略为自定义，允许通过信号触发菜单显示
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            # 连接 customContextMenuRequested 信号到 _show_right_menu 槽函数

            if self._right_menu_connected:
                try:
                    self.customContextMenuRequested.disconnect(self._show_right_menu)
                except Exception:
                    pass
                self._right_menu_connected = False

            self.customContextMenuRequested.connect(self._show_right_menu)
            self._right_menu_connected = True

        # --- 处理鼠标左键点击 ---
        elif button == Qt.MouseButton.LeftButton:
            event.accept()

        # 如果是其他鼠标按钮（例如中键），则不执行任何操作

    def mouseReleaseEvent(self, event) -> None:
        """
        处理鼠标按钮松开事件，主要用于调用主界面。
        """
        # 只响应左键的松开事件
        if event.button() != Qt.MouseButton.LeftButton:
            return  # 忽略非左键的释放

        self._show_bugsy()
        # 左键释放事件通常不需要 event.accept()

    def _show_bugsy(self) -> None:
        buggy.show_main_window(self.App)
        pass

    def _init_widget(self) -> None:
        """
        初始化窗口的基本属性：设置为无边框、总在最前、半透明的子窗口。
        同时初始化与鼠标拖动相关的状态变量。
        """
        # --- 窗口样式与行为设置 ---
        # 组合窗口标志：无边框，总在最前，作为子窗口（通常用于不显示在任务栏）
        # 使用 "|" 操作符合并多个标志位
        window_flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SubWindow
        self.setWindowFlags(window_flags)

        # 设置背景透明
        self.setAutoFillBackground(False)  # 禁用自动填充背景，配合下面的透明属性
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # 启用窗口透明效果

        # --- 鼠标交互状态初始化 ---
        # 这两个变量用于实现窗口拖动功能
        self.is_follow_mouse: bool = False  # 初始状态：不跟随鼠标
        # mouse_drag_pos 在 mousePressEvent 中会被正确设置，这里初始化为当前位置
        self.mouse_drag_pos: QPoint = self.pos()

        self.repaint()

    def _init_ui(self):
        """
        初始化用户界面元素及其布局。
        """

        # ============================================================
        # 1. 宠物动画显示区域
        # ============================================================
        # 用于显示宠物动画的主要标签
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.label.installEventFilter(self)  # 安装事件过滤器

        # ============================================================
        # 3. 对话框显示区域
        # ============================================================
        self.dialogue_box = QHBoxLayout()
        self.dialogue_box.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.dialogue_box.setContentsMargins(0, 0, 0, 0)

        # 对话框背景
        self.dialogue = QLabel(self)
        self.dialogue.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 对话框背景，并设置大小
        image = QImage()
        image.load('Pet/res/icons/text_frame.png')
        # print(f"image.width: {image.width()}, image.height: {image.height()}")
        self.dialogue.setFixedWidth(image.width())
        self.dialogue.setFixedHeight(image.height())

        # 设置字体
        QFontDatabase.addApplicationFont('Pet/res/font/MFNaiSi_Noncommercial-Regular.otf')
        font = QFont('华文楷体', int(15 / screen_scale))
        self.dialogue.setFont(font)

        # 开启自动换行
        self.dialogue.setWordWrap(True)

        # 设置最大宽度，使得每行显示不超过12个汉字（按汉字宽度预估）
        char_width = font.pointSize() * 1.2  # 估算每个汉字的宽度（可微调）
        max_chars_per_line = 12
        max_width = int(char_width * max_chars_per_line)
        self.dialogue.setMaximumWidth(max_width)

        self.dialogue.setStyleSheet("""
            background-image: url(Pet/res/icons/text_frame.png);
            color: black;
        """)

        self.dialogue_box.addWidget(self.dialogue)

        # ============================================================
        # 4. 主窗口布局设置
        # ============================================================
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 宠物布局
        self.petlayout = QVBoxLayout()
        self.petlayout.addWidget(self.label)
        self.petlayout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.petlayout.setContentsMargins(0, 0, 0, 0)

        # 将对话框布局和宠物布局添加到主布局中
        # 注意添加顺序：对话框在上方 (视觉上可能在旁边，取决于整体窗口设计)，宠物布局在下方
        self.layout.addLayout(self.dialogue_box, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.layout.addLayout(self.petlayout, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)

        # 设置主布局
        self.setLayout(self.layout)

    def _set_menu(self, pets=()):
        """
        初始化并设置右键菜单及其所有动作和子菜单。
        """
        # 1. 创建主菜单对象
        menu = QMenu(self)

        # ============================================================
        # 2. 添加 "切换角色" 子菜单
        # ============================================================
        # --- 创建子菜单 ---
        change_menu = QMenu(menu)
        change_menu.setTitle('切换角色')

        # --- 动态创建并添加角色动作 ---
        # 使用辅助函数 _build_act 为每个宠物名称创建一个 QAction
        # 并将其连接到 self._change_pet 槽函数
        change_acts = [_build_act(name, change_menu, self._change_pet) for name in pets]
        change_menu.addActions(change_acts)

        # --- 将子菜单添加到主菜单 ---
        menu.addMenu(change_menu)

        # ============================================================
        # 3. 添加 "选择动作" 子菜单 (条件性添加)
        # ============================================================
        # 仅当 self.pet_conf.random_act_name 存在时才添加此子菜单
        if self.pet_conf.random_act_name is not None:
            # --- 创建子菜单 ---
            act_menu = QMenu(menu)
            act_menu.setTitle('选择动作')

            # --- 动态创建并添加动作 ---
            # 使用辅助函数 _build_act 为每个动作名称创建一个 QAction
            # 并将其连接到 self._show_act 槽函数
            select_acts = [
                _build_act(name, act_menu, self._show_act)
                for name in self.pet_conf.random_act_name
            ]
            act_menu.addActions(select_acts)

            # --- 将子菜单添加到主菜单 ---
            menu.addMenu(act_menu)

        # ============================================================
        # 4. 添加分隔符
        # ============================================================
        menu.addSeparator()

        # ============================================================
        # 5. 添加 "救救我" 动作
        # ============================================================
        debug_menu = QAction('救救我！', menu)
        debug_menu.triggered.connect(self._show_bugsy)
        menu.addAction(debug_menu)

        # ============================================================
        # 6. 添加 "退出" 动作
        # ============================================================
        quit_act = QAction('退出', menu)  # 创建动作
        quit_act.triggered.connect(self.quit)  # 连接信号
        menu.addAction(quit_act)  # 直接添加到主菜单

        # ============================================================
        # 7. 将构建好的菜单赋给实例变量
        # ============================================================
        self.menu = menu

    def _show_right_menu(self):
        """
        在当前鼠标光标的位置弹出预先设置好的右键菜单 (self.menu)。
        确保 self.menu 对象已在调用此方法前被正确创建和配置。
        """
        # 光标位置弹出菜单
        self.menu.popup(QCursor.pos())

    def _change_pet(self, pet_name: str) -> None:
        """
        切换当前显示的宠物。

        此过程按顺序执行以下操作：
        1. 停止与当前宠物相关的所有活动线程。
        2. 加载并初始化新选定宠物的配置和资源。
        3. 请求界面重绘。
        4. 启动新宠物的核心活动线程。
        5. 更新 UI 元素以匹配新宠物。
        """
        # 步骤 1: 停止当前宠物的所有相关活动线程
        # -----------------------------------------
        # 确保在加载新宠物配置前，旧宠物的后台任务已停止
        self.stop_thread('Animation')  # 停止动画线程
        self.stop_thread('Interaction')  # 停止交互线程
        self.stop_thread('Scheduler')  # 停止计划线程

        # 清除可能存在的旧对话框
        self._set_dialogue_dp('None')
        settings.showing_dialogue_now = False

        # 步骤 2: 加载并初始化新宠物的配置和资源
        self.init_conf(pet_name)

        # 步骤 3: 请求界面重绘
        self.repaint()

        # 步骤 4: 启动新宠物的核心活动线程
        # -----------------------------------------
        self.run_animation()
        self.run_interaction()
        self.run_scheduler()

        # 步骤 5: 更新 UI 元素以匹配新宠物
        if hasattr(self, '_setup_ui') and callable(getattr(self, '_setup_ui')):
            self._setup_ui(self.pic_dict)
        else:
            print(
                f"警告：方法 _setup_ui 未找到或不可调用。跳过 _change_pet 中的 UI 初始化步骤。 "
            )

    def init_conf(self, pet_name: str) -> None:
        """
        根据指定的宠物名称，初始化窗口和宠物的核心配置。
        1. 设置当前宠物名称 (`self.curr_pet_name`)。
        2. 加载该宠物的所有图像资源 (`self.pic_dict`)。
        3. 加载或创建该宠物的配置对象 (`self.pet_conf`)。
        4. 计算用于布局调整的边距值 (`self.margin_value`)。
        5. 加载或初始化该宠物的状态数据 (`self.pet_data`)。
        6. 更新依赖于当前宠物配置的UI组件 (菜单 `self._set_menu` 和系统托盘 `self._set_tray`)。
        """
        # 1. 设置当前宠物标识与加载核心资源/配置
        # -----------------------------------------
        self.curr_pet_name = pet_name
        self.pic_dict = _load_all_pic(pet_name)
        self.pet_conf = PetConfig.init_config(self.curr_pet_name, self.pic_dict)

        # 2. 计算用于布局调整的边距值
        # -----------------------------------------
        self.margin_value = 0.5 * max(
            self.pet_conf.width, self.pet_conf.height
        )  # 用于将widgets调整到合适的大小

        # 3. 加载或初始化该宠物的状态数据
        # -----------------------------------------
        self.pet_data = PetData(self.curr_pet_name)

        # 4. 更新依赖于当前宠物配置的UI组件
        # -----------------------------------------
        if hasattr(self, 'pets'):
            self._set_menu(self.pets)
        else:
            print(f"警告：未找到self.pets属性，无法在init_conf中更新菜单。")

        # 更新系统托盘
        self._set_tray()

    def _setup_ui(self, pic_dict):
        """
        根据当前宠物的配置 (self.pet_conf) 和传入的图片字典 (pic_dict)，
        调整界面元素的尺寸、设置初始值、更新显示图片、定位窗口，并初始化特定子任务。
        通常在宠物切换或初始化时调用。
        """

        # 1. 调整主窗口尺寸
        # -------------------
        # 设置整个窗口的固定尺寸。
        # 宽度 = 宠物宽度 + 边距值
        # 高度 = 对话框高度 + 边距值 + 固定偏移(60) + 宠物高度
        self.setFixedSize(
            int(self.pet_conf.width + self.margin_value),
            int(self.dialogue.height() + self.margin_value + 60 + self.pet_conf.height),
        )


        # 2. 更新宠物显示的图片
        # -----------------------
        settings.previous_img = settings.current_img
        if pic_dict:  # 确保 pic_dict 不为空
            settings.current_img = list(pic_dict.values())[0]
        else:
            print("警告：pic_dict 为空，无法设置当前图片。")

        self.set_img()
        self.border = self.pet_conf.width / 2

        # 3. 设置窗口的初始位置
        # ---------------------
        # 获取屏幕可用几何区域 (排除任务栏等)
        screen_geo = QGuiApplication.primaryScreen().availableGeometry()
        screen_width = screen_geo.width()
        work_height = screen_geo.height()

        # 计算窗口的初始位置
        x = int(screen_width * 0.8)
        # y 坐标计算方式使得窗口底部与屏幕可用区域的底部对齐
        y = work_height - self.height()

        self.floor_pos = work_height - self.height()
        self.move(x, y)

    def eventFilter(self, watched_object, event):
        return False

    def _set_tray(self) -> None:
        """
        设置或更新应用程序在系统托盘中的图标及其关联菜单。

        - 如果 `self.tray` 尚未初始化 (值为 `None`)，则进行首次创建和设置。
        - 如果 `self.tray` 已存在，则仅更新其上下文菜单 (`self.menu`) 并确保其可见。

        依赖 `self.menu` 已经被正确设置。
        """
        if self.tray is None:
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(QIcon('Pet/res/icons/icon.png'))
            # 将预设的右键菜单 (self.menu) 关联到托盘图标
            self.tray.setContextMenu(self.menu)
            self.tray.show()
        else:
            # 1. 仅更新托盘图标关联的右键菜单
            #    这允许在程序运行时动态改变菜单内容（例如切换宠物后更新菜单项）
            self.tray.setContextMenu(self.menu)

            # 2. 确保托盘图标是可见的
            #    即使之前已经调用过 show(), 再次调用通常无害，
            #    可以确保图标处于显示状态（以防万一被隐藏）。
            print("显示系统托盘")
            self.tray.show()

    def set_img(self):  # , img: QImage) -> None:
        """
        根据 `settings.current_img` 中存储的图像数据 (预期为 QImage)，
        更新 `self.label` 控件以显示该图片，并调整其尺寸。

        同时，将该图像数据也存储在 `self.image` 属性中。
        """
        # 1. 调整 QLabel (self.label) 的尺寸以完全匹配新图像的宽度和高度
        #    确保标签大小正好能容纳整个图片
        try:
            image_width = settings.current_img.width()
            image_height = settings.current_img.height()
            self.label.resize(image_width, image_height)
        except AttributeError:
            print(
                f"错误：无法从 settings.current_img 获取尺寸。请确保它是一个有效的 QImage 对象。"
            )
            # 可以选择在这里返回或设置一个默认图片/尺寸
            return

        # 2. 将 QImage (settings.current_img) 转换为 QPixmap 并设置为 QLabel 的内容
        #    QPixmap 是专门用于在屏幕上显示的优化图像格式
        self.label.setPixmap(QPixmap.fromImage(settings.current_img))

        # 3. 将当前的 QImage 对象也保存到实例变量 self.image 中
        #    这个副本的具体用途需要结合其他使用 self.image 的代码来理解
        self.image = settings.current_img

    def _set_dialogue_dp(self, texts='None'):
        """
        设置或隐藏对话框标签 (self.dialogue) 的文本内容。

        - 如果传入的 `texts` 参数是字符串 'None' (区分大小写)，则隐藏对话框。
        - 否则，使用 `text_wrap` 函数处理传入的文本（例如自动换行），
          然后将处理后的文本设置到对话框标签上，并显示该标签。

        依赖外部函数 `text_wrap` 来进行文本格式化处理。
        """
        # print("dialogue size:", self.dialogue.size())
        # print(f"texts: {texts}")
        # 检查传入的文本是否等于特定的哨兵字符串 'None'
        if texts == 'None':
            # 如果 texts 是 'None'，则隐藏对话框控件
            self.dialogue.hide()

        else:
            # 1. 使用外部函数 text_wrap 处理文本格式 (例如：自动换行)
            #    确保 text_wrap 函数已定义或导入，并且能正确处理输入
            try:
                texts_wrapped = text_wrap(texts)
            except NameError:
                # print(f"错误：text_wrap 函数未定义！将使用原始文本。")
                texts_wrapped = texts  # 如果 text_wrap 不可用，则回退到原始文本
            except Exception as e:
                # print(f"错误：调用 text_wrap 时出错: {e}。将使用原始文本。")
                texts_wrapped = texts  # 其他异常也回退

            # 2. 将处理（或原始）后的文本设置到对话框标签上
            self.dialogue.setText(texts_wrapped)

            # 3. 显示对话框标签，使其可见
            self.dialogue.show()
            # print("have shown dialogue")

    def _change_status(self, status: str, change_value: float):
        pass

    def _change_time(self, status, timeleft):
        pass

    def quit(self) -> None:
        """
        关闭应用程序窗口并终止整个Python进程。

        执行顺序：
        1. 调用 `self.close()` 来关闭与此对象关联的窗口（通常是主窗口）。
           这会触发窗口的关闭事件 (closeEvent)，允许进行清理操作。
        2. 调用 `sys.exit()` 来请求Python解释器退出。
        """
        try:
            # 步骤 1: 关闭窗口
            # 这会发送一个关闭事件给窗口，允许正常的清理流程
            self.stop_scheduler()
            self.stop_interaction()
            self.close()

            # 步骤 2: 退出应用程序进程
            # 强制终止 Python 解释器
            sys.exit()

        except Exception as e:
            print(f"[错误] quit: 在尝试关闭窗口或退出程序时发生错误: {e}")
            # 即使出错，可能仍需尝试强制退出
            try:
                sys.exit(1)  # 尝试以非零状态码退出，表示异常终止
            except SystemExit:
                pass  # 忽略 sys.exit() 本身引发的 SystemExit 异常
            except Exception as exit_e:
                print(f"[严重错误] quit: 尝试强制退出也失败了: {exit_e}")

    def stop_thread(self, module_name):
        """
        停止指定模块关联的后台工作线程。

        执行步骤：
        1. 尝试调用工作者对象 (`self.workers[module_name]`) 的 `kill()` 方法 (如果存在)。
           这通常用于通知工作者内部逻辑停止。
        2. 尝试调用线程对象 (`self.threads[module_name]`) 的 `terminate()` 方法。
           这是一个更强制的停止方式，可能不会进行清理。
        3. 调用线程对象 (`self.threads[module_name]`) 的 `wait()` 方法。
           阻塞当前流程，直到目标线程完全终止。
        """
        try:
            # 检查 worker 和 thread 是否存在于字典中
            if module_name not in self.workers:
                print(f"[错误] stop_thread: 未找到名为 '{module_name}' 的工作者对象。")
                # 根据需要决定是否继续尝试停止线程，或者直接返回
                # 此处假设如果 worker 不存在，可能 thread 也不可靠或不需停止
                # return
            if module_name not in self.threads:
                print(f"[错误] stop_thread: 未找到名为 '{module_name}' 的线程对象。")
                return  # 如果线程对象不存在，无法继续

            worker = self.workers[module_name]
            thread = self.threads[module_name]

            # 步骤 1: 尝试调用 worker 的 kill 方法
            if hasattr(worker, 'kill') and callable(worker.kill):
                worker.kill()
            else:
                # 如果没有 kill 方法，可能无法停止，依赖 terminate
                pass

            # 步骤 2: 终止线程 (强制停止)
            if hasattr(thread, 'terminate') and callable(thread.terminate):
                thread.terminate()
            else:
                print(
                    f"[错误] stop_thread: 线程对象 '{module_name}' 没有 terminate 方法。"
                )
                # 如果无法 terminate，可能也无法 wait，但仍尝试 wait

            # 步骤 3: 等待线程结束
            if hasattr(thread, 'wait') and callable(thread.wait):
                thread.wait()
            else:
                print(f"[错误] stop_thread: 线程对象 '{module_name}' 没有 wait 方法。")

        except KeyError:
            print(
                f"[错误] stop_thread: 提供的模块名 '{module_name}' 在 workers 或 threads 字典中不存在。"
            )
        except AttributeError as e:
            print(
                f"[错误] stop_thread: 尝试调用 kill/terminate/wait 时出错，对象可能不符合预期结构: {e}"
            )
        except Exception as e:
            print(f"[错误] stop_thread: 停止线程 '{module_name}' 时发生意外错误: {e}")

    def fall_onoff(self):
        pass

    def show_tomato(self):
        pass

    def run_tomato(self, nt):
        pass

    def change_tomato_menu(self):
        pass

    def show_focus(self):
        pass

    def run_focus(self, task: str, hs, ms):
        pass

    def change_focus_menu(self):
        pass

    def show_remind(self):
        pass

    def run_remind(self, task_type, hs=0, ms=0, texts=''):
        pass

    def run_animation(self):
        """
        初始化并启动动画处理的后台线程和工作者对象。

        执行步骤：
        1. 创建一个新的 QThread 对象并存储在 `self.threads['Animation']`。
        2. 创建一个 `Animation_worker` 实例 (传入宠物配置) 并存储在 `self.workers['Animation']`。
        3. 将 `Animation_worker` 移动到新创建的线程中。
        4. 连接线程的 `started` 信号到工作者的 `run` 方法。
        5. 连接工作者发出的信号 (`sig_setimg_anim`, `sig_move_anim`, `sig_repaint_anim`)
           到主线程中对应的槽函数 (`self.set_img`, `self._move_customized`, `self.repaint`)。
        6. 启动线程。
        7. 允许线程被外部终止 (setTerminationEnabled)。
        """
        module_name = 'Animation'

        try:
            # --- 核心逻辑 ---
            # 1. 创建线程对象
            self.threads[module_name] = QThread()

            # 2. 创建工作者对象
            #    需要确保 Animation_worker 类可用且构造函数接受 self.pet_conf
            if (
                'AnimationWorker' not in globals()
                and 'AnimationWorker' not in locals()
            ):
                print(
                    f"[错误] runAnimation: 'AnimationWorker' 类未定义或导入。无法创建工作者。"
                )
                # 清理已创建的线程对象
                del self.threads[module_name]
                return
            try:
                self.workers[module_name] = AnimationWorker(self.pet_conf)
            except Exception as e:
                print(f"[错误] runAnimation: 创建 'AnimationWorker' 实例失败: {e}")
                del self.threads[module_name]  # 清理线程
                return

            # 3. 移动到线程
            self.workers[module_name].moveToThread(self.threads[module_name])

            # 4. 连接线程启动信号到工作者运行方法
            self.threads[module_name].started.connect(self.workers[module_name].run)

            # 5. 连接工作者信号到主线程槽函数
            #    需要确保 worker 有这些信号，主线程有这些槽函数
            worker = self.workers[module_name]
            if hasattr(worker, 'sig_set_img_anim'):
                worker.sig_set_img_anim.connect(self.set_img)
            else:
                print(
                    f"[警告] runAnimation: AnimationWorker 缺少 sig_set_img_anim 信号。"
                )

            if hasattr(worker, 'sig_move_anim'):
                worker.sig_move_anim.connect(self._move_customized)
            else:
                print(
                    f"[警告] runAnimation: AnimationWorker 缺少 sig_move_anim 信号。"
                )

            if hasattr(worker, 'sig_repaint_anim'):
                worker.sig_repaint_anim.connect(self.repaint)
            else:
                print(
                    f"[警告] runAnimation: AnimationWorker 缺少 sig_repaint_anim 信号。"
                )

            # 6. 启动线程
            self.threads[module_name].start()

            # 7. 设置线程可终止
            self.threads[module_name].setTerminationEnabled()

        except KeyError as e:
            print(
                f"[错误] runAnimation: 访问字典 key 时出错: {e}。可能发生在线程/worker未成功创建。"
            )
        except TypeError as e:
            # 例如，connect 时信号或槽不匹配，或 moveToThread 参数错误
            print(
                f"[错误] runAnimation: 类型错误: {e}。可能发生在信号槽连接或对象移动时。"
            )
        except Exception as e:
            # 捕获其他所有意外错误
            print(f"[错误] runAnimation: 启动动画线程时发生未知错误: {e}")
            # 尝试清理，防止留下部分初始化的状态
            if module_name in self.threads:
                del self.threads[module_name]
            if module_name in self.workers:
                del self.workers[module_name]

    def run_interaction(self):
        """
        初始化并启动交互处理的后台线程和工作者对象。

        执行步骤：
        1. 创建一个新的 QThread 对象并存储在 `self.threads['Interaction']`。
        2. 创建一个 `Interaction_worker` 实例 (传入宠物配置) 并存储在 `self.workers['Interaction']`。
        3. 将 `Interaction_worker` 移动到新创建的线程中。
        4. 连接工作者发出的信号 (`sig_setimg_inter`, `sig_move_inter`, `sig_act_finished`)
           到主线程中对应的槽函数 (`self.set_img`, `self._move_customized`, `self.resume_animation`)。
        5. 启动线程。
        6. 允许线程被外部终止 (setTerminationEnabled)。
        """
        module_name = 'Interaction'
        try:
            # --- 核心逻辑 ---
            # 1. 创建线程
            self.threads[module_name] = QThread()

            # 2. 创建
            try:
                self.workers[module_name] = Interaction_worker(self.pet_conf)
            except Exception as e:
                print(f"[错误] runInteraction: 创建 'Interaction_worker' 实例失败: {e}")
                del self.threads[module_name]
                return

            # 3. 移动到线程
            self.workers[module_name].moveToThread(self.threads[module_name])

            # 4. 连接工作者信号到主线程槽
            worker = self.workers[module_name]
            if hasattr(worker, 'sig_set_img_inter'):
                worker.sig_set_img_inter.connect(self.set_img)
            else:
                print(
                    f"[警告] runInteraction: Interaction_worker 缺少 sig_set_img_inter 信号。"
                )

            if hasattr(worker, 'sig_move_inter'):
                worker.sig_move_inter.connect(self._move_customized)
            else:
                print(
                    f"[警告] runInteraction: Interaction_worker 缺少 sig_move_inter 信号。"
                )

            if hasattr(worker, 'sig_act_finished'):
                worker.sig_act_finished.connect(self.resume_animation)
            else:
                print(
                    f"[警告] runInteraction: Interaction_worker 缺少 sig_act_finished 信号。"
                )

            # 6. 启动线程
            self.threads[module_name].start()

            # 7. 设置线程可终止
            self.threads[module_name].setTerminationEnabled()

        except KeyError as e:
            print(f"[错误] runInteraction: 访问字典 key 时出错: {e}。")
        except TypeError as e:
            print(f"[错误] runInteraction: 类型错误: {e}。")
        except Exception as e:
            print(f"[错误] runInteraction: 启动交互线程时发生未知错误: {e}")
            if module_name in self.threads:
                del self.threads[module_name]
            if module_name in self.workers:
                del self.workers[module_name]

    def run_scheduler(self):
        """
        初始化并启动计划任务处理的后台线程和工作者对象。
        执行步骤：
        1. 创建一个新的 QThread 对象并存储在 `self.threads['Scheduler']`。
        2. 创建一个 `Scheduler_worker` 实例 (传入宠物配置) 并存储在 `self.workers['Scheduler']`。
        3. 连接调度器线程(`self.threads['Scheduler']`) 的 `started` 信号到工作者的 `run` 方法。
        4. 连接 `Scheduler_worker` 发出的多个信号到主线程中对应的槽函数。
        5. 启动调度器线程(`self.threads['Scheduler']`)。
        6. 允许调度器线程被外部终止。
        """
        module_name = 'Scheduler'

        try:
            # --- 核心逻辑 ---
            # 1. 创建调度器线程
            self.threads[module_name] = QThread()

            # 2. 创建调度器工作者
            try:
                self.workers[module_name] = Scheduler_worker(self.pet_conf)
            except Exception as e:
                print(f"[错误] runScheduler: 创建 'Scheduler_worker' 实例失败: {e}")
                del self.threads[module_name]
                return

            self.workers[module_name].moveToThread(
                self.threads[module_name]###
            )

            # 3. 连接调度器线程的 started 到 run (可能行为异常，见步骤3注释)
            self.threads[module_name].started.connect(
                self.workers[module_name].run
            )

            # 4. 连接工作者信号到主线程槽
            worker = self.workers[module_name]
            signals_to_connect = {
                'sig_settext_sche': self._set_dialogue_dp,
                'sig_setact_sche': self._show_act,
                'sig_setstat_sche': self._change_status,
                'sig_focus_end': self.change_focus_menu,
                'sig_tomato_end': self.change_tomato_menu,
                'sig_settime_sche': self._change_time,
            }
            for signal_name, slot_func in signals_to_connect.items():
                if hasattr(worker, signal_name):
                    getattr(worker, signal_name).connect(slot_func)
                else:
                    print(
                        f"[警告] runScheduler: Scheduler_worker 缺少 {signal_name} 信号。"
                    )

            # 5. 启动调度器线程
            self.threads[module_name].start()

            # 6. 设置调度器线程可终止
            self.threads[module_name].setTerminationEnabled()

        except KeyError as e:
            print(
                f"[错误] runScheduler: 访问字典 key 时出错: {e} (可能是 Interaction 线程不存在，或线程/worker未成功创建)。"
            )
        except TypeError as e:
            print(f"[错误] runScheduler: 类型错误: {e}。")
        except Exception as e:
            print(f"[错误] runScheduler: 启动计划任务线程时发生未知错误: {e}")
            if module_name in self.threads:
                del self.threads[module_name]
            if module_name in self.workers:
                del self.workers[module_name]

    def stop_scheduler(self):
        self.workers['Scheduler'].kill()  # 设置终止标志
        self.threads['Scheduler'].quit()  # 请求线程退出
        self.threads['Scheduler'].wait()  # 等待线程真正结束

    def stop_interaction(self):
        self.workers['Interaction'].kill()  # 设置终止标志
        self.threads['Interaction'].quit()  # 请求线程退出
        self.threads['Interaction'].wait()  # 等待线程真正结束

    def _move_customized(self, plus_x, plus_y):
        """
        根据给定的偏移量 (`plus_x`, `plus_y`) 移动窗口，并处理边界碰撞逻辑。

        行为包括：
        - 水平方向：如果窗口移出屏幕边界，则实现循环滚动（从一边消失，从另一边出现）。
        - 垂直方向：
            - 如果窗口尝试移动到屏幕顶部以上，则限制其位置。 (原代码逻辑是限制在 y=0 以下)
            - 如果窗口移动到或低于预设的"地面"位置 (`self.floor_pos`)，则将其固定在地面上。
            - 当首次接触地面时 (`settings.onfloor == 0` 变为 1)，会重置宠物图片为默认站立图，
              并尝试恢复动画 (`self.workers['Animation'].resume()`)。
        """
        try:
            # --- 核心逻辑 ---
            current_pos = self.pos()

            # 计算初步的新坐标
            new_x = current_pos.x() + plus_x
            new_y = current_pos.y() + plus_y

            # 1. 水平边界处理 (循环滚动)
            # -------------------------
            win_width = self.width()  # 获取窗口宽度

            # 判断是否超出左边界 (考虑边距 self.border)
            if new_x + win_width < self.border:
                new_x = self.screen_width + self.border - win_width

            # 判断是否超出右边界 (考虑边距 self.border)
            elif new_x > self.screen_width + self.border - win_width:
                new_x = self.border - win_width

            # 2. 垂直边界处理
            # -----------------
            # 限制不能移到屏幕顶部以上 (原代码判断 y+border < 0，可能依赖border含义)
            if new_y + self.border < 0:  # 简单的顶部限制
                new_y = self.floor_pos  # 固定在顶部
                # print(f"[调试信息] 碰到上边界, new_y 重置为 {new_y}") # 仅用于调试，发布时删除

            # 判断是否接触或低于地面
            elif new_y >= self.floor_pos:
                new_y = self.floor_pos  # 固定在地面上

            # 3. 应用最终计算出的位置
            # -----------------------
            self.move(int(new_x), int(new_y))  # 确保传入整数

        except (TypeError, ValueError) as e:
            # 捕获 plus_x/y 非数值，或 int() 转换失败等错误
            print(
                f"[错误] _move_customized: 计算新位置时发生类型或值错误: {e}。输入: plus_x={plus_x}, plus_y={plus_y}"
            )
        except AttributeError as e:
            # 捕获 前置检查 后，实际访问 self 属性/方法时仍可能发生的错误
            print(f"[错误] _move_customized: 访问对象属性或方法时出错: {e}。")
        except KeyError as e:
            # 捕获访问 self.workers['Animation'] 时 key 不存在的错误
            print(f"[错误] _move_customized: 访问 workers 字典时键错误: {e}。")
        except Exception as e:
            # 捕获其他所有意外错误
            print(f"[错误] _move_customized: 执行移动时发生未知错误: {e}")

    def _show_act(self, random_act_name):
        """
        触发一个特定的交互动作。

        执行步骤：
        1. 暂停当前的常规动画 (`self.workers['Animation'].pause()`)。
        2. 启动交互工作者 (`self.workers['Interaction']`) 来执行指定的动作 (`random_act_name`)。
           交互动作通常是临时的，完成后会通过信号 (`sig_act_finished`) 通知主流程恢复常规动画。
        """
        # 1. 暂停动画
        self.workers['Animation'].pause()
        # 2. 启动交互
        self.workers['Interaction'].start_interact('animat', random_act_name)

    def resume_animation(self):
        """
        恢复（或继续执行）常规的动画循环。

        通常在交互动作完成 (`sig_act_finished` 信号触发) 后被调用，
        或者在需要手动恢复动画的场景下使用。
        """
        self.workers['Animation'].resume()


def _load_all_pic(pet_name: str) -> dict:
    """
    加载指定宠物名称对应的所有动作图片资源。

    函数会查找 'res/role/{pet_name}/action/' 目录下的所有图片文件，
    并将它们加载为图片对象 (通过 `_get_q_img` 函数)。
    返回一个字典，其中键是动作名称 (通常是去掉扩展名的文件名)，值是加载的图片对象。
    """
    # 1. 构建图片目录路径
    img_dir = 'Pet/res/role/{}/action/'.format(pet_name)
    # 2. 列出目录中的所有文件/目录
    images = os.listdir(img_dir)
    # 3. 返回成功加载的图片字典
    return {image.split('.')[0]: _get_q_img(img_dir + image) for image in images}


def _build_act(name: str, parent: QObject, act_func) -> QAction:
    """
    构建一个 QAction 对象（菜单项或工具栏按钮）。
    """
    try:
        # 1. 创建 QAction 实例
        act = QAction(name, parent)

        # 2. 连接 triggered 信号到 lambda 函数
        act.triggered.connect(lambda: act_func(name))

        # 3. 返回创建的 Action
        return act

    except TypeError as e:
        # 主要捕获 QAction 构造或 connect 时因参数类型错误引发的问题
        print(f"[错误] _build_act: 创建 QAction '{name}' 失败，类型错误: {e}")
        return None
    except Exception as e:
        # 捕获其他未知错误
        print(f"[错误] _build_act: 创建 QAction '{name}' 时发生未知错误: {e}")
        return None


def _get_q_img(img_path: str) -> Optional[QImage]:
    """
    从指定的路径加载图片为 QImage 对象。
    """
    try:
        # 1. 创建空的 QImage 对象
        image = QImage()

        # 2. 尝试加载图片
        #    QImage.load() 会返回 bool 值指示成功与否
        if image.load(img_path):
            # 3. 加载成功，返回 QImage 对象
            return image
        else:
            # 4. 加载失败 (文件格式不支持、文件损坏等)
            print(
                f"[警告] _get_q_img: 无法加载图片 (可能格式不支持或文件损坏): '{img_path}'"
            )
            return None  # 返回 None 表示失败

    except Exception as e:
        # 捕获 QImage 构造、load 或 os.path.isfile 中可能发生的其他意外错误
        print(f"[错误] _get_q_img: 加载图片 '{img_path}' 时发生未知错误: {e}")
        return None


def text_wrap(texts: str, line_length: int = 7) -> str:
    """
    将输入字符串按指定行长度进行换行处理。
    """
    try:
        n_char = len(texts)
        # 计算需要的行数 (向上取整)
        n_line = (n_char + line_length - 1) // line_length

        texts_wrapped = ''
        # 逐行构建包装后的文本
        for i in range(n_line):
            start_index = line_length * i
            # 使用切片获取当前行的子字符串，min() 确保不会超出字符串末尾
            end_index = min(start_index + line_length, n_char)
            texts_wrapped += texts[start_index:end_index] + '\n'

        # 移除末尾多余的换行符
        texts_wrapped = texts_wrapped.rstrip('\n')

        return texts_wrapped

    except Exception as e:
        # 捕获在长度计算、切片或拼接中可能出现的意外错误
        print(f"[错误] text_wrap: 处理文本换行时发生未知错误: {e}")
        return ''  # 返回空字符串表示失败


if __name__ == '__main__':
    """
    应用程序主入口点。
    加载宠物数据，创建并显示宠物窗口。
    """
    pets_data = None
    app = None  # 初始化为 None，便于 finally 中检查

    try:
        # 1. 加载宠物数据
        pets_file = 'data/pets.json'
        try:
            pets_data = read_json(pets_file)
            if not pets_data:
                print(f"[错误] 未能从 '{pets_file}' 加载有效的宠物数据。")
                sys.exit(1)  # 数据加载失败，无法继续，退出
        except FileNotFoundError:
            print(f"[错误] 宠物数据文件未找到: '{pets_file}'")
            sys.exit(1)
        except Exception as e:  # 捕获 JSON 解析错误或其他 read_json 内部错误
            print(f"[错误] 加载或解析宠物数据 '{pets_file}' 时失败: {e}")
            sys.exit(1)

        # 2. 创建 Qt Application 实例
        app = QApplication(sys.argv)

        # 3. 创建主窗口部件 (PetWidget)
        p = PetWidget(pets=pets_data)

        # 4. 启动 Qt 事件循环
        exit_code = app.exec_()
        sys.exit(exit_code)  # 使用 Qt 应用的退出码退出

    except ImportError as e:
        print(f"[严重错误] 缺少必要的库: {e}。")
        sys.exit(1)
    except NameError as e:
        print(f"[严重错误] 必要的类或函数未定义: {e}。")
        sys.exit(1)
    except Exception as e:
        print(f"[严重错误] 应用程序启动或运行时发生未知错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)  # 发生严重错误，以错误码退出
