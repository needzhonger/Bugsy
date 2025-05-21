from PySide6.QtGui import QFont
from common import *

log = logging.getLogger(__name__)

common_font = QFont()  # 用于普通的文字，0
common_font.setFamilies(["Segoe UI", "Helvetica", "Arial"])
common_font.setPointSize(13)

big_font = QFont()  # 用于较大的文字，1
big_font.setFamilies(["Segoe UI", "Helvetica", "Arial"])
big_font.setPointSize(15)

title_font = QFont()  # 用于应用名的字体，2
title_font.setFamilies(["Inter", "Helvetica Neue", "Segoe UI", "Arial"])
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