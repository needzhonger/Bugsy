from camel.embeddings import SentenceTransformerEncoder
from camel.retrievers import VectorRetriever
from camel.storages.vectordb_storages import QdrantStorage
from .FileReader import extract_text_auto
from .common import *

log = logging.getLogger(__name__)


class RAGStorage:
	"""用于RAG"""

	def __init__(
			self,
			model_name="BAAI/bge-small-zh-v1.5",
			collection_name="RAG_files_collection",
			path="RAG_files",
			similarity_threshold=0.5,
			top_k=1,
			chunker=None
	):
		"""
		:param collection_name: collection的地址
		:param path: 文件夹的地址
		:param similarity_threshold: 检索时的相似度阈值
		:param top_k: 给出前top_k个相关的结果
		"""
		# embedding模型
		self.encoder = SentenceTransformerEncoder(model_name=model_name)

		self.similarity_threshold = similarity_threshold
		self.top_k = top_k
		self.chunker = chunker

		# Create or initialize a vector storage
		self.vector_storage = QdrantStorage(
			vector_dim=self.encoder.get_output_dim(),
			collection_name=collection_name,
			path=path,
		)

		# Initialize the VectorRetriever with an embedding model
		self.vr = VectorRetriever(self.encoder, self.vector_storage)

	def process_file(self, content_input_path):
		"""读取文件内容，支持txt,pdf,docx，仅支持文本"""
		success, raw_text = extract_text_auto(content_input_path)
		if success:
			self.vr.process(
				content=raw_text,  # 传入的是文件的内容
				chunk_type="chunk_by_title",  # 按标题分块
				max_characters=1000,  # 分块容量
				extra_info={"source": content_input_path},
				metadata_filename=content_input_path,
				chunker=self.chunker,  # 使用自定义分块器
			)
		else:
			# TODO:与前端连接
			log.error(f"不支持的文件类型: {content_input_path}")

	def process_url(self, path):
		"""读取网址"""
		self.vr.process(
			content=path,  # 传入的是网址
			chunk_type="chunk_by_title",  # 按标题分块
			max_characters=1000,  # 分块容量
			extra_info={"source": path},
			metadata_filename=path,
			chunker=self.chunker,  # 使用自定义分块器
		)

	def query(self, query):
		"""查询"""
		result = self.vr.query(query, self.top_k, self.similarity_threshold)
		return self.to_readable(result)

	def to_readable(self, results):
		if not results:
			return "未找到相关信息"

		readable = []
		for result in results:
			text = result.get("text", "")
			if text[:39] == "No suitable information retrieved from ":
				return "没有相关文件"
			source = result.get("extra_info", {}).get("source", "未知文件")
			readable.append(
				f"【文件来源】{source}\n"
				f"【相关内容】\n{text}\n"
				f"【匹配度】{float(result.get('similarity score', 0)):.2f}\n"
				"-----"
			)
		return "\n".join(readable)


if __name__ == '__main__':
	rag_storage = RAGStorage(similarity_threshold=0.6, top_k=1)

	while True:
		order = input("\n添加文件:1    添加网址:2    搜索已添加的内容:3\n")
		if order == '1':
			content_path = input("Provide the path to our content input (can be a file or URL)\n")
			rag_storage.process_file(content_path)
		elif order == '2':
			content_path = input("Provide the path to our content input (can be a file or URL)\n")
			rag_storage.process_url(content_path)
		elif order == '3':
			qry = input("Specify your query\n")
			print(rag_storage.query(qry))
		else:
			continue
