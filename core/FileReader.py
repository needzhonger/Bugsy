import magic
import fitz
from docx import Document
from .common import *

log = logging.getLogger('FileReader')


def extract_text_auto(file_path):
	"""
	自动识别文件类型并提取文本
	:param file_path: 文件路径
	:return: 文本内容
	"""
	# 检测文件类型
	mime = magic.Magic(mime=True)
	file_type = mime.from_file(file_path)

	# 根据类型调用对应函数
	if file_type == "application/pdf":
		return extract_pdf_text(file_path)
	elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
		return extract_docx_text(file_path)
	elif file_type == "text/plain":
		return extract_txt_text(file_path)
	else:
		log.error(f"不支持的文件类型: {file_type}")
		return False, None


def extract_pdf_text(pdf_path):
	"""
	提取 PDF 文件中的所有文本内容
	:param pdf_path: PDF 文件路径
	:return: 字符串形式的文本内容
	"""
	text = ""
	success = True
	try:
		with fitz.open(pdf_path) as doc:
			for page in doc:
				text += page.get_text()
	except Exception as e:
		log.error(f"PDF 解析失败: {e}")
		success = False
	return success, text


def extract_docx_text(docx_path):
	"""
	提取 DOCX 文件中的所有文本内容
	:param docx_path: DOCX 文件路径
	:return: 字符串形式的文本内容
	"""
	text = ""
	success = True
	try:
		doc = Document(docx_path)
		for para in doc.paragraphs:
			text += para.text + "\n"
	except Exception as e:
		log.error(f"DOCX 解析失败: {e}")
		success = False
	return success, text.strip()


def extract_txt_text(txt_path, encoding="utf-8"):
	"""
	提取 TXT 文件内容（自动处理编码问题）
	:param txt_path: TXT 文件路径
	:param encoding: 文件编码（默认utf-8，可选gbk等）
	:return: 字符串形式的文本内容
	"""
	success = True
	text = None
	try:
		with open(txt_path, "r", encoding=encoding) as f:
			text = f.read()
	except UnicodeDecodeError:
		# 尝试 fallback 到 gbk 编码（常见于中文文件）
		try:
			with open(txt_path, "r", encoding="gbk") as f:
				text = f.read()
		except Exception as e:
			log.error(f"TXT 解析失败: {e}")
			success = False
	except Exception as e:
		log.error(f"TXT 读取失败: {e}")
		success = False
	return success, text

if __name__=='__main__':
	while True:
		print(extract_text_auto(input("输入文件地址（英文）\n"))[1])