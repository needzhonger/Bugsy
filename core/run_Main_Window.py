from PySide6.QtCore import Qt

from .common import *
from .MainWindow import MainWindow

have_MainWindow = False
main_window = None

def init_platform_style(app):
	# 根据系统选择UI风格
	if sys.platform == "win32":
		app.setStyle(QStyleFactory.create("windows"))
	elif sys.platform == "darwin":
		app.setStyle(QStyleFactory.create("macintosh"))

logging.basicConfig(
	level=logging.INFO,  # 设置最低日志级别
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式
	handlers=[
		logging.StreamHandler(sys.stdout),  # 输出到控制台
	]
)

def show_main_window(app = None):
	global have_MainWindow
	global main_window
	if not have_MainWindow:
		main_window = MainWindow(app, 1000, 600)
		have_MainWindow = True
	main_window.show()
	# 1. 取消最小化（恢复正常大小）
	main_window.setWindowState(main_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)

	# 2. 置顶显示
	main_window.raise_()  # 提升到其他窗口上方
	main_window.activateWindow()  # 激活为当前活动窗口

if __name__ == "__main__":
	show_main_window(QApplication([]))