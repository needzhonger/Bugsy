from common import *
from MainWindow import MainWindow


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

if __name__ == "__main__":
	app = QApplication([])
	init_platform_style(app)
	app.setWindowIcon(QIcon("pic/todolist.png"))
	main_window = MainWindow(app, 1000, 600)
	main_window.show()
	app.exec()