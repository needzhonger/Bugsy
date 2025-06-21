import tempfile
from .common import *
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsPixmapItem
from PySide6.QtGui import QPixmap, QImage
from PIL import Image


class Screenshot(QWidget):
	"""
	接口:1)调用:打开一个新窗口来调用，进行图片选择
    2)发送信号:通过self.image_signal来发送图片,类型:pil
	"""
	image_signal = Signal(object)  # 传输PIL.Image对象给ImageAgent

	def __init__(self):
		super().__init__()
		self.setWindowTitle("截图工具")
		self.setFixedSize(300, 300)

		# 初始化变量
		self.save_path = os.path.expanduser("~/Pictures")
		self.current_image_path = None
		self.temp_image_path = os.path.join(tempfile.gettempdir(), f"qtshot_{os.getpid()}.png")

		# 主界面
		layout = QVBoxLayout(self)

		_label = QLabel('    请使用系统截图工具（如Win+Shift+S）截图后返回本程序')
		_label.setWordWrap(True)
		layout.addWidget(_label)

		# 预览区域
		self.preview_scene = QGraphicsScene()
		self.preview_view = QGraphicsView()
		self.preview_view.setScene(self.preview_scene)
		layout.addWidget(self.preview_view)

		btn_layout = QHBoxLayout()
		layout.addLayout(btn_layout)
		# 截图按钮
		self.capture_btn = QPushButton("刷新")
		self.capture_btn.clicked.connect(self.capture_to_clipboard)
		btn_layout.addWidget(self.capture_btn)

		# 发送按钮
		self.copy_btn = QPushButton("OK")
		self.copy_btn.clicked.connect(self.picture_processing)
		btn_layout.addWidget(self.copy_btn)

		# 剪贴板监控定时器
		self.clipboard_timer = QTimer()
		self.clipboard_timer.timeout.connect(self.check_clipboard)

		# 样式设置
		self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid palette(mid);
                padding: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: palette(midlight); /*轻微高亮*/
                border-radius: 4px;
            }
            QPushButton:pressed {
				background-color: palette(light);
			}
            QGraphicsView { border: 1px solid #ddd; }
        """)

		# 跟踪所有临时文件
		self.temp_files = []

	def capture_to_clipboard(self):
		"""调用系统截图工具（需提前截图到剪贴板）"""
		self.clipboard_timer.start(500)  # 开始监控剪贴板

	def check_clipboard(self):
		"""检查剪贴板中是否有图像"""
		clipboard = QApplication.clipboard()
		mime_data = clipboard.mimeData()

		if mime_data.hasImage():
			# 获取图像并转换为QPixmap
			image = clipboard.image()
			if not image.isNull():
				# 保存到临时文件
				if image.save(self.temp_image_path, "PNG"):
					self.current_image_path = self.temp_image_path
					pixmap = QPixmap.fromImage(image)

					# 更新界面
					self.preview_scene.clear()
					pixmap_item = self.preview_scene.addPixmap(pixmap)
					self.preview_view.fitInView(pixmap_item, Qt.KeepAspectRatio)  # 自动缩放适配视图

					self.clipboard_timer.stop()  # 找到图像后停止监控
					self.temp_files.append(self.temp_image_path)  # 记录新临时文件

					# 打印调试信息
					print(f"截图已保存到：{self.temp_image_path}")

	def picture_processing(self):
		"""将当前图像转换为PIL.Image并通过信号传输"""
		items = self.preview_scene.items()
		if items and isinstance(items[0], QGraphicsPixmapItem):
			# 获取QPixmap
			qt_pixmap = items[0].pixmap()

			# 转换为QImage
			qt_image = qt_pixmap.toImage()

			# 转换为PIL.Image
			pil_image = self.qt_image_to_pil(qt_image)
			if pil_image == 0:
				QMessageBox.warning(self, '警告', '所选的图像为空图像')
				return
			elif pil_image == 1:
				QMessageBox.warning(self, '警告', '图像转换失败')
				return

			# 发送图片
			self.send_image_signal(pil_image)

			# 保留原有功能：同时复制到系统剪贴板
			QApplication.clipboard().setPixmap(qt_pixmap)

			# 关闭窗口
			self.close()

	def send_image_signal(self, pil_image):
		"""通过信号发送PIL.Image对象"""
		self.image_signal.emit(pil_image)

	def qt_image_to_pil(self, qt_image):
		"""将图像转化为pil类型，以发送给AI"""
		if qt_image.isNull():
			return 0
		if qt_image.format() != QImage.Format.Format_RGBA8888:
			qt_image = qt_image.convertToFormat(QImage.Format.Format_RGBA8888)
			if qt_image.isNull():
				return 1
		return Image.frombytes(
			"RGBA",
			(qt_image.width(), qt_image.height()),
			qt_image.constBits().tobytes(),
			'raw', "RGBA"
		)

	def closeEvent(self, event):
		"""重写关闭事件处理"""
		for file in self.temp_files:
			try:
				if os.path.exists(file):
					os.unlink(file)
			except Exception as e:
				print(f"删除临时文件失败: {e}")
		super().closeEvent(event)


if __name__ == "__main__":
	app = QApplication([])
	window = Screenshot()

	window.image_signal.connect(lambda img: print(f"接收到PIL.Image对象，尺寸: {img.size}"))

	window.show()
	app.exec()
