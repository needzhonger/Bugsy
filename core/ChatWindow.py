from html import escape
from .common import *
from markdown import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from bleach import clean
from bleach.css_sanitizer import CSSSanitizer
from .Signals import Signals
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class ChatMessage(QWidget):
	def __init__(self, message, is_me, avatar_path=None, parent=None):
		super().__init__(parent)
		self.is_me = is_me
		self.full_html = ""
		self.setup_ui(message)

	def setup_ui(self, message):
		if old_layout := self.layout():
			temp_widget = QWidget()
			temp_widget.setLayout(old_layout)
			old_layout.deleteLater()

		layout = QHBoxLayout()
		margin = int(self.fontMetrics().averageCharWidth() * 3)
		layout.setContentsMargins(margin, 8, margin, 8)

		self.full_html = self.safe_markdown_conversion(message)

		self.message_label = SafeQLabel(self.full_html, self)
		self.message_label.setMinimumHeight(40)
		self.message_label.configure_style(self.is_me)

		layout.addWidget(self.message_label, 1)
		self.setLayout(layout)

	def append_message(self, new_message):

		try:
			merged_content = f"{self.extract_raw_content()}\n{new_message}"
			self.full_html = self.safe_markdown_conversion(merged_content)
			self.message_label.set_html_content(self.full_html)
			self.adjustSize()
		except Exception as e:
			log.error(f"消息追加失败: {str(e)}")
			self.message_label.set_text_content(f"<span style='color:red'>消息渲染错误: {escape(str(e))}</span>")

	def extract_raw_content(self):
		soup = BeautifulSoup(self.full_html, 'html.parser')
		for tag in soup(['style', 'script']):
			tag.decompose()
		return soup.get_text(separator='\n').strip()

	def safe_markdown_conversion(self, markdown_text):
		try:
			if not isinstance(markdown_text, str):
				raise ValueError("非文本类型输入")

			sanitized = self.sanitize_input(markdown_text)

			html_content = self.convert_markdown(sanitized)
			highlighted = self.add_code_highlight(html_content)
			styled = self.wrap_full_html(highlighted)

			return styled
		except Exception as e:
			log.exception("Markdown处理失败")
			return f"""
            <div class='error-box'>
                <p> 内容渲染错误</p>
                <pre>{escape(str(e))}</pre>
                <hr>
                <pre>原始内容: {escape(markdown_text[:500])}</pre>
            </div>
            """


	def convert_markdown(self, text):
		try:
			return markdown(
				text,
				extensions=[
					'fenced_code',
					'codehilite',
					'tables',
					'nl2br',
				],
				output_format='html5'
			)
		except Exception as e:
			raise RuntimeError(f"文档转换失败: {str(e)}") from e

	def add_code_highlight(self, html):
		try:
			soup = BeautifulSoup(html, 'html.parser')
			formatter = HtmlFormatter(
				style="material",
				noclasses=True,
				cssstyles="""
                    background: #f8f9fa !important; 
                    border-radius: 4px;
                    padding: 1em;
                    margin: 1em 0;
                    overflow-x: auto;
                """
			)

			for pre_tag in soup.find_all('pre'):
				code_tag = pre_tag.find('code')
				if not code_tag:
					continue

				lang = 'text'
				classes = code_tag.get('class', [])
				if classes:
					lang_class = next((c for c in classes if c.startswith('language-')), None)
					if lang_class:
						lang = lang_class.split('-')[-1]

				try:
					lexer = get_lexer_by_name(lang, stripall=True)
				except ClassNotFound:
					lexer = TextLexer()

				try:
					highlighted = highlight(
						code_tag.get_text(),
						lexer,
						formatter
					)
					new_tag = soup.new_tag('div')
					new_tag.append(BeautifulSoup(highlighted, 'html.parser'))
					pre_tag.replace_with(new_tag)
				except Exception as e:
					log.warning(f"代码高亮失败: {str(e)}")
					error_tag = soup.new_tag('div', style='color:red;')
					error_tag.string = f"代码高亮错误: {str(e)}"
					pre_tag.replace_with(error_tag)

			return str(soup)
		except Exception as e:
			log.error(f"HTML处理异常: {str(e)}")
			return html

	def wrap_full_html(self, content):
		return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            {HtmlFormatter(style="material").get_style_defs('.highlight')}
            body {{
                margin:0;
                font-family: system-ui, -apple-system, sans-serif;
                line-height: 1.6;
                font-size: 15px;
                color: {'#222' if self.is_me else '#444'};
            }}
            .error-box {{
                background: #fff0f0;
                border: 1px solid #ffb3b3;
                padding: 1em;
                border-radius: 4px;
            }}
            pre {{
                background: #f8f9fa !important;
                border-radius: 4px !important;
                margin: 1em 0 !important;
                padding: 1em !important;
                overflow-x: auto;
            }}
            code {{ 
                padding: 0.2em 0.4em;
                background: #f8f9fa;
                border-radius: 3px;
            }}
            table {{
                border-collapse: collapse;
                margin: 1em 0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            th, td {{ padding: 0.75em; border: 1px solid #dee2e6; }}
            th {{ background: #f8f9fa; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            img {{ max-width: 100%; height: auto; }}
            .highlight {{
                background: transparent !important;
                padding: 0 !important;
                margin: 0 !important;
            }}
        </style>
        </head>
        <body>{content}</body>
        </html>
        """

	def sanitize_input(self, text):
		return clean(
			escape(text),
			tags=[
				'p', 'pre', 'code', 'blockquote', 'ul', 'ol', 'li',
				'strong', 'em', 'a', 'img', 'table', 'thead', 'tbody',
				'tr', 'th', 'td', 'br', 'hr', 'h1', 'h2', 'h3', 'div',
				'span', 'details', 'summary'
			],
			attributes={
				'a': ['href', 'title', 'rel'],
				'img': ['src', 'alt', 'title', 'width', 'height'],
				'div': ['class'],
				'span': ['class'],
				'details': ['open'],
				'*': ['style']
			},
			protocols=['http', 'https', 'data'],
			strip_comments=True,
			css_sanitizer=CSSSanitizer(
				allowed_css_properties=['color', 'font-weight', 'text-decoration']
			)
		)


class SafeQLabel(QLabel):

	def __init__(self, html, parent):
		super().__init__(parent)
		self.setWordWrap(True)
		self.setTextFormat(Qt.RichText)
		self.setTextInteractionFlags(Qt.TextBrowserInteraction)
		self.setOpenExternalLinks(True)
		self._html_content = ""
		self.set_html_content(html)
		self.setSizePolicy(
			QSizePolicy.Expanding,
			QSizePolicy.Preferred
		)


	def set_html_content(self, html):
		self._html_content = html
		self.setHtml(html)

	def configure_style(self, is_me):
		self.setStyleSheet(f"""
				QLabel {{
					background: {'#d1f7c4' if is_me else '#ffffff'};
					border-radius: 8px;
					padding: 12px;
					border: 1px solid rgba(0,0,0,0.1);
					color: {'#222' if is_me else '#444'};
					margin: 0;
				}}
				QLabel a {{ color: {'#1a6b1d' if is_me else '#0366d6'}; }}
			""")

	def set_text_content(self, text):
		self.setText(text)


class ChatList(QListWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.last_sender = None
		self.setStyleSheet("""
            QListWidget {
                background: #f8f9fa;
                border: none;
                outline: none;
            }
            QListWidget::item { 
                margin: 6px 0;
                border: none;
            }
        """)
		self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
		self.verticalScrollBar().setSingleStep(20)
		self.setSpacing(4)

	def receive_message(self, content, is_me):
		try:
			if not isinstance(content, str) or not content.strip():
				raise ValueError("无效消息内容")

			content = content.replace('\x00', '').strip()

			if self.should_append(is_me):
				self.append_to_last(content, is_me)
			else:
				self.create_new_item(content, is_me)

			if is_me:
				self.send_message(content)

			self.scrollToBottom()
		except Exception as e:
			log.error(f"消息处理失败: {str(e)}")
			self.show_error_message(str(e))



	def should_append(self, is_me):
		return (
				self.last_sender == is_me and
				self.count() > 0 and
				(item := self.item(self.count() - 1)) and
				(widget := self.itemWidget(item))
		)


	def append_to_last(self, content, is_me):
		last_item = self.item(self.count() - 1)
		widget = self.itemWidget(last_item)
		try:
			widget.append_message(content)
			last_item.setSizeHint(widget.sizeHint())
		except Exception as e:
			log.error(f"消息追加失败: {str(e)}")
			self.create_new_item(f"[原始消息追加失败，显示为新消息]\n{content}", is_me)


	def create_new_item(self, content, is_me):
		item = QListWidgetItem()
		widget = ChatMessage(content, is_me)
		item.setSizeHint(widget.sizeHint())
		self.addItem(item)
		self.setItemWidget(item, widget)
		self.last_sender = is_me



	def create_new_item(self, content, is_me):
		item = QListWidgetItem()
		widget = ChatMessage(content, is_me)
		item.setSizeHint(widget.sizeHint())
		self.addItem(item)
		self.setItemWidget(item, widget)
		self.last_sender = is_me


	def show_error_message(self, error):
		item = QListWidgetItem()
		widget = QLabel(f"<span style='color:red'> 错误: {escape(error)}</span>")
		widget.setStyleSheet("padding: 8px;")
		item.setSizeHint(widget.sizeHint())
		self.addItem(item)
		self.setItemWidget(item, widget)


	def send_message(self, content):
		Signals.instance().send_message_to_ai(content)


if __name__ == "__main__":
	from PySide6.QtWidgets import QApplication
	import sys

	logging.basicConfig(level=logging.INFO)

	app = QApplication(sys.argv)
	Signals.instance().chat_agent_response_signal.connect(lambda msg: print(f"AI收到消息: {msg}"))

	chat_list = ChatList()
	chat_list.receive_message("用户消息测试", True)
	chat_list.receive_message("这是一条markdown测试：\n\n```python\nprint('Hello World!')\n```", True)

	window = QWidget()
	layout = QHBoxLayout()
	layout.addWidget(chat_list)
	window.setLayout(layout)
	window.resize(600, 400)
	window.show()

	sys.exit(app.exec())
