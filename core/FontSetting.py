from PySide6.QtGui import QFont
from common import *

log = logging.getLogger(__name__)

# 普通字体，适合正文和按钮等，微软雅黑为主，兼容宋体和黑体
common_font = QFont()
common_font.setFamilies(["华文楷体", "KaiTi", "楷体", "SimKai", "微软雅黑"])
common_font.setPointSize(13)

# 较大字体，用于稍微重要点的文字，比如按钮标题
big_font = QFont()
big_font.setFamilies(["华文楷体", "KaiTi", "楷体", "SimKai", "微软雅黑"])
big_font.setPointSize(15)

# 标题字体，华文楷体为首选，兼容楷体、宋体等
title_font = QFont()
title_font.setFamilies(["华文楷体", "KaiTi", "楷体", "SimKai", "微软雅黑"])
title_font.setPointSize(20)

def set_font(my_widget, kind=0):
	"""
	设置init中有的字体字体，以常用程度排序
	"""
	if kind == 0:
		my_widget.setFont(common_font)
	elif kind == 1:
		my_widget.setFont(big_font)
	elif kind == 2:
		my_widget.setFont(title_font)
	else:
		print("FontSetting @ set_font:警告：使用未知字体！")