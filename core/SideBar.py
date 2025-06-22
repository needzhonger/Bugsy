from .common import *
from .Signals import Signals
from .FontSetting import set_font
from functools import partial


class SideBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)

        self.setStyleSheet(
            """QFrame{
                           background-color:#D1D9E0
                           }"""
        )

        # ===侧边栏内容===
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 20)

        name_label = QLabel("Bugsy\n————————")
        name_label.setAlignment(Qt.AlignCenter)
        set_font(name_label, 2)
        layout.addWidget(name_label)

        # 把sidebar撑开
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addItem(spacer)

        # ===添加功能按钮===
        names = ("Debug", "文字输入", "图片输入", "文件输入")
        _names = (
            "ChattingWindow1",
            "ChattingWindow2",
            "ChattingWindow3",
            "ChattingWindow4",
        )
        for i in range(len(names)):
            btn = QPushButton(f"{names[i]}")
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 25px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: palette(midlight); /*轻微高亮*/
                    border-radius: 4px;
                }
                QPushButton:pressed {
					background-color: palette(light);
				}
            """
            )
            set_font(btn, 1)
            layout.addWidget(btn)
            # 连接按钮与切换页面信号
            btn.clicked.connect(
                partial(Signals.instance().send_page_change_signal, _names[i])
            )
        layout.addStretch()
        self.setLayout(layout)
