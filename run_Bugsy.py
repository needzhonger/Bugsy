# -*- coding: utf-8 -*-
"""
Pet 桌面宠物应用启动脚本。

该脚本负责加载宠物数据，初始化 PyQt5 应用，
应用自定义样式表，并创建和显示主宠物窗口 (PetWidget)。
"""

import sys

from PySide6.QtWidgets import QApplication

from Pet.Petaler import PetWidget
from Pet.utils import read_json


def show_pet():
    """
    应用程序的主入口点。
    负责加载数据、创建应用实例、设置样式并运行主窗口。
    """
    # 1. 加载宠物数据
    try:
        pets_data = read_json('Pet/data/pets.json')
        print("宠物数据加载成功。")
    except FileNotFoundError:
        print("错误：找不到宠物数据文件 'data/pets.json'。请确保文件存在。")
        sys.exit(1)
    except Exception as e:
        print(f"加载宠物数据时发生错误: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    print("正在创建宠物窗口...")
    pet_widget = PetWidget(pets=pets_data, App = app)
    print("宠物窗口已创建。")

    print("启动应用程序事件循环...")
    sys.exit(app.exec())


if __name__ == '__main__':
    show_pet()
